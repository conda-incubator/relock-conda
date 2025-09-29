from collections.abc import Mapping
import os
import pprint
import shutil
import subprocess
import sys
import tempfile

import click
from conda.models.match_spec import MatchSpec
from ruamel.yaml import YAML

yaml = YAML(typ="safe", pure=True)
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.default_flow_style = False


def _split_package_list(package_list):
    packages = []
    for nline in package_list.split("\n"):
        for cline in nline.split(","):
            for sline in cline.split():
                _pkg = sline.strip()
                if _pkg:
                    packages.append(_pkg)
    return packages


def _lock_to_ver(lock, platform):
    pkg_to_ver = {}
    for pkg in lock["package"]:
        if pkg["platform"] == platform:
            pkg_to_ver[pkg["name"]] = pkg["version"]
    return pkg_to_ver


@click.command()
@click.option("--environment-file", required=True, type=click.Path(exists=True))
@click.option("--lock-file", required=True, type=click.Path())
@click.option("--ignored-packages", required=True, type=str)
@click.option("--relock-all-packages", required=True, type=str)
@click.option("--include-only-packages", required=True, type=str)
@click.option("--merge-as-admin-packages", required=True, type=str)
def main(
    environment_file,
    lock_file,
    ignored_packages,
    relock_all_packages,
    include_only_packages,
    merge_as_admin_packages,
):
    merge_as_admin = False
    relocked = False
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            ignored_packages = _split_package_list(ignored_packages)
            relock_all_packages = relock_all_packages.lower() == "true"
            merge_as_admin_packages = _split_package_list(merge_as_admin_packages)
            include_only_packages = _split_package_list(include_only_packages)

            have_existing_lock_file = os.path.exists(lock_file)

            backup_lock_file = os.path.join(tmpdir, os.path.basename(lock_file))
            if have_existing_lock_file:
                shutil.move(lock_file, backup_lock_file)
            else:
                print(
                    "No existing lock file found. Creating a new one.",
                    flush=True,
                    file=sys.stderr,
                )

            print("Relocking environment.yml...", flush=True, file=sys.stderr)
            subprocess.run(
                ["conda", "lock", "--file", environment_file, "--lockfile", lock_file],
                check=True,
                capture_output=True,
            )

            if not have_existing_lock_file:
                print(
                    "A lock file has been created in this PR since no existing one was found.",
                    flush=True,
                )
                relocked = True
            else:
                with open(environment_file) as f:
                    envyml = yaml.load(f)

                with open(backup_lock_file) as f:
                    old_lock = yaml.load(f)

                with open(lock_file) as f:
                    new_lock = yaml.load(f)

                old_platform_pkg_to_ver = {
                    platform: _lock_to_ver(old_lock, platform)
                    for platform in envyml["platforms"]
                }

                new_platform_pkg_to_ver = {
                    platform: _lock_to_ver(new_lock, platform)
                    for platform in envyml["platforms"]
                }

                if relock_all_packages:
                    deps_to_relock = set()
                    for platform in envyml["platforms"]:
                        for pkg in new_platform_pkg_to_ver[platform]:
                            deps_to_relock.add(pkg)
                elif include_only_packages:
                    deps_to_relock = set(include_only_packages)
                else:
                    deps_to_relock = set()
                    for _spec in envyml["dependencies"]:
                        if not isinstance(_spec, Mapping):
                            deps_to_relock.add(MatchSpec(_spec).name)
                        else:
                            for _pkg in _spec:
                                deps_to_relock.add(MatchSpec(_pkg).name)

                print(
                    "relock all packages:",
                    relock_all_packages,
                    flush=True,
                    file=sys.stderr,
                )
                print(
                    "initial deps to relock:\n",
                    pprint.pformat(deps_to_relock),
                    flush=True,
                    file=sys.stderr,
                )
                print(
                    "ignored packages:\n",
                    pprint.pformat(ignored_packages),
                    flush=True,
                    file=sys.stderr,
                )
                print(
                    "include only packages:\n",
                    pprint.pformat(include_only_packages),
                    flush=True,
                    file=sys.stderr,
                )
                print(
                    "merge as admin packages:\n",
                    pprint.pformat(merge_as_admin_packages),
                    flush=True,
                    file=sys.stderr,
                )

                deps_to_relock = deps_to_relock - set(ignored_packages)

                print(
                    "final deps to relock:\n",
                    pprint.pformat(deps_to_relock),
                    flush=True,
                    file=sys.stderr,
                )

                relock_tuples = {platform: [] for platform in envyml["platforms"]}
                for pkg in deps_to_relock:
                    for platform in envyml["platforms"]:
                        if old_platform_pkg_to_ver[platform].get(
                            pkg
                        ) != new_platform_pkg_to_ver[platform].get(pkg):
                            relock_tuples[platform].append(
                                (
                                    pkg,
                                    old_platform_pkg_to_ver[platform].get(pkg),
                                    new_platform_pkg_to_ver[platform].get(pkg),
                                )
                            )

                if any(relock_tuples[platform] for platform in envyml["platforms"]):
                    if all(
                        all(
                            tup[0] in merge_as_admin_packages
                            for tup in relock_tuples[platform]
                        )
                        for platform in envyml["platforms"]
                    ):
                        merge_as_admin = True

                    msg = "The following packages have been updated:\n\n"
                    for platform in envyml["platforms"]:
                        _curr_tuples = sorted(
                            relock_tuples[platform], key=lambda tup: tup[0]
                        )
                        msg += f"  * platform: {platform}\n"
                        for pkg, old_ver, new_ver in _curr_tuples:
                            msg += f"      - {pkg}: {old_ver} -> {new_ver}\n"
                        msg += "\n"

                    if relock_all_packages:
                        msg += (
                            "Note: All package updates, even those not to a dependency "
                            f"listed in your '{environment_file}' file, are listed above because you "
                            "requested that all packages be relocked.\n"
                        )

                    print(msg, flush=True, file=sys.stderr)
                    print(msg, flush=True)

                    relocked = True
                else:
                    print("No packages have been updated.", flush=True, file=sys.stderr)
                    shutil.move(backup_lock_file, lock_file)
                    relocked = False
        except Exception as e:
            if os.path.exists(backup_lock_file) and have_existing_lock_file:
                shutil.move(backup_lock_file, lock_file)

            subprocess.run(
                'echo "env_relocked=false" >> "$GITHUB_OUTPUT"',
                shell=True,
            )

            subprocess.run(
                f'echo "merge_as_admin={"true" if merge_as_admin else "false"}" >> "$GITHUB_OUTPUT"',
                shell=True,
            )

            raise e

    subprocess.run(
        f'echo "env_relocked={"true" if relocked else "false"}" >> "$GITHUB_OUTPUT"',
        shell=True,
    )
    subprocess.run(
        f'echo "merge_as_admin={"true" if merge_as_admin else "false"}" >> "$GITHUB_OUTPUT"',
        shell=True,
    )


if __name__ == "__main__":
    main()
