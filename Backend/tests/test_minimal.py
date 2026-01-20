def test_import():
    """Test if security module can be imported"""
    import sys
    print(f"\nsys.path = {sys.path[:3]}")
    
    # Try importing security
    import security
    print(f"security module path: {security.__file__}")
    
    # Try importing audit_logger
    from security.audit_logger import PIIRedactor
    print(f"PIIRedactor: {PIIRedactor}")
    
    assert True
