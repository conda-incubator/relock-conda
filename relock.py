import os
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


def _lock_to_ver(lock, platform):
    pkg_to_ver = {}
    for pkg in lock["package"]:
        if pkg["platform"] == platform:
            pkg_to_ver[pkg["name"]] = pkg["version"]
    return pkg_to_ver


def _reformat_lockfile(lockfile):
    # load / dump the lockfile to make sure it is sorted
    # so we get nice diffs
    with open(lockfile) as f:
        new_lock = yaml.load(f)
    new_lock["package"] = sorted(
        new_lock["package"], key=lambda x: (x["name"], x["platform"])
    )
    with open(lockfile, "w") as f:
        yaml.dump(new_lock, f)

    with open(lockfile) as f:
        lines = [line.rstrip() for line in f]

    with open(lockfile, "w") as f:
        f.write("\n".join(lines) + "\n")


@click.command()
@click.option("--environment-file", required=True, type=click.Path(exists=True))
@click.option("--lock-file", required=True, type=click.Path())
@click.option("--ignored-packages", required=True, type=str)
@click.option("--relock-all-packages", required=True, type=str)
def main(environment_file, lock_file, ignored_packages, relock_all_packages):
    ignored_packages = [pkg.strip() for pkg in ignored_packages.split(",")]
    relock_all_packages = relock_all_packages.lower() == "true"

    have_existing_lock_file = os.path.exists(lock_file)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
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
                ["conda", "lock", "--file", environment_file],
                check=True,
                capture_output=True,
            )

            if not have_existing_lock_file:
                print(
                    "A lock file has been created in this PR since no existing one was found.",
                    flush=True,
                )
            else:
                with open("environment.yml") as f:
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
                else:
                    deps_to_relock = set()
                    for _spec in envyml["dependencies"]:
                        deps_to_relock.add(MatchSpec(_spec).name)

                deps_to_relock = deps_to_relock - set(ignored_packages)

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
                    _reformat_lockfile(lock_file)

                    if any(relock_tuples[platform] for platform in envyml["platforms"]):
                        print("The following packages have been updated:\n", flush=True)
                        for platform in envyml["platforms"]:
                            print(f"  platform: {platform}", flush=True)
                            for pkg, old_ver, new_ver in relock_tuples[platform]:
                                print(
                                    f"    - {pkg}: {old_ver} -> {new_ver}", flush=True
                                )
                            print("", flush=True)
                else:
                    print("No packages have been updated.", flush=True, file=sys.stderr)
                    shutil.move(backup_lock_file, lock_file)
        except Exception as e:
            if os.path.exists(backup_lock_file) and have_existing_lock_file:
                shutil.move(shutil.move(backup_lock_file, lock_file))
            raise e


if __name__ == "__main__":
    main()
