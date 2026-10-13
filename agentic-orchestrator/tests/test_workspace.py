import pytest
from app import workspace

def test_path_traversal_rejected():
    for value in ("../../etc/passwd", "/etc/passwd", "../secret.yml", "src/main/../../../../evil.java"):
        with pytest.raises(ValueError):workspace.file_path(value)

def test_inspection_returns_source():
    assert any(name.endswith("pom.xml") for name in workspace.inspect())

def test_invalid_change_cannot_modify_files():
    with pytest.raises(ValueError):workspace.apply_changes([{"path":"../../evil.java","content":"bad"}])
