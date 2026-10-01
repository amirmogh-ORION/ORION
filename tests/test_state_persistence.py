import subprocess


def test_persistence_keeps_archives_not_present_in_application_checkout(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()
    git("init")
    git("config", "user.name", "ORION test")
    git("config", "user.email", "test@localhost")
    cycles = tmp_path/"reports/cycles"
    cycles.mkdir(parents=True)
    (cycles/"old.json").write_text('{"cycle":"old"}')
    git("add", ".")
    git("commit", "-m", "prior persisted cycle")
    parent = git("rev-parse", "HEAD")
    # The application checkout contains the new report, not old state-branch files.
    (cycles/"old.json").unlink()
    (cycles/"new.json").write_text('{"cycle":"new"}')
    git("read-tree", "--empty")
    git("read-tree", parent)
    git("add", "-f", "reports/cycles/new.json")
    tree = git("write-tree")
    names = git("ls-tree", "-r", "--name-only", tree).splitlines()
    assert "reports/cycles/old.json" in names
    assert "reports/cycles/new.json" in names
