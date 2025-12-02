"""
SQL WHERE Clause Validator Tests

Tests for SQL injection prevention with 37 comprehensive test cases
covering exact matches, fuzzy matches, and all security scenarios.
"""
import pytest
from src.utils.sql_validator import SQLWhereValidator, validate_where_clause

# Mark all tests in this file as unit and security tests
pytestmark = [pytest.mark.unit, pytest.mark.security]


class TestSQLWhereValidator:
    """Test SQL validation rules"""
    
    # ==================== VALID CLAUSES ====================
    
    def test_valid_simple_ilike(self):
        """Test valid simple ILIKE query"""
        clause = "title ILIKE '%python%'"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"
    
    def test_valid_multiple_conditions_and(self):
        """Test valid multiple conditions with AND"""
        clause = "title ILIKE '%python%' AND genre = 'Technology'"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"
    
    def test_valid_multiple_conditions_or(self):
        """Test valid multiple conditions with OR"""
        clause = "title ILIKE '%python%' OR description ILIKE '%programming%'"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"
    
    def test_valid_with_parentheses(self):
        """Test valid query with parentheses for grouping"""
        clause = "(title ILIKE '%python%' OR description ILIKE '%python%') AND genre = 'Technology'"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"
    
    def test_valid_author_search(self):
        """Test valid author search"""
        clause = "author ILIKE '%stephen king%'"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"
    
    def test_valid_not_ilike(self):
        """Test valid NOT ILIKE"""
        clause = "title NOT ILIKE '%test%'"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"
    
    def test_valid_comparison_operators(self):
        """Test valid comparison operators"""
        clause = "genre = 'Fiction'"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"
    
    def test_valid_extract_year(self):
        """Test valid EXTRACT for year"""
        clause = "EXTRACT(YEAR FROM published_date) = 2020"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"
    
    # ==================== INJECTION ATTEMPTS ====================
    
    def test_reject_delete(self):
        """Test rejection of DELETE"""
        clause = "title ILIKE '%test%'; DELETE FROM books"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "Multiple statements" in msg or "DELETE" in msg
    
    def test_reject_drop(self):
        """Test rejection of DROP"""
        clause = "title ILIKE '%test%' OR 1=1; DROP TABLE books"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_reject_union(self):
        """Test rejection of UNION"""
        clause = "title ILIKE '%test%' UNION SELECT * FROM users"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "UNION" in msg
    
    def test_reject_update(self):
        """Test rejection of UPDATE"""
        clause = "title ILIKE '%test%'; UPDATE books SET price=0"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_reject_insert(self):
        """Test rejection of INSERT"""
        clause = "title ILIKE '%test%'; INSERT INTO books VALUES (...)"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_reject_subquery(self):
        """Test rejection of subqueries"""
        clause = "title IN (SELECT title FROM books WHERE id > 10)"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "Subqueries" in msg
    
    def test_reject_sql_comments(self):
        """Test rejection of SQL comments"""
        clause = "title ILIKE '%test%' -- malicious comment"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "comments" in msg.lower()
    
    def test_reject_block_comments(self):
        """Test rejection of block comments"""
        clause = "title ILIKE '%test%' /* comment */"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "comments" in msg.lower()
    
    def test_reject_multiple_statements(self):
        """Test rejection of multiple statements"""
        clause = "title ILIKE '%test%'; SELECT * FROM users"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "Multiple statements" in msg
    
    def test_reject_invalid_column(self):
        """Test rejection of invalid column names"""
        clause = "password ILIKE '%admin%'"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "Column" in msg and "not allowed" in msg
    
    def test_reject_unbalanced_parentheses(self):
        """Test rejection of unbalanced parentheses"""
        clause = "(title ILIKE '%test%' AND genre = 'Fiction'"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "parentheses" in msg.lower()
    
    def test_reject_dangerous_functions(self):
        """Test rejection of dangerous SQL functions"""
        clause = "title ILIKE CONCAT('%', 'test', '%')"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "functions" in msg.lower()
    
    def test_reject_exec(self):
        """Test rejection of EXEC"""
        clause = "EXEC sp_executesql 'malicious code'"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "EXEC" in msg
    
    def test_reject_alter(self):
        """Test rejection of ALTER"""
        clause = "title ILIKE '%test%'; ALTER TABLE books ADD COLUMN hacked INT"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_reject_join(self):
        """Test rejection of JOIN"""
        clause = "books.title ILIKE '%test%' JOIN users ON books.user_id = users.id"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "JOIN" in msg
    
    # ==================== EDGE CASES ====================
    
    def test_reject_empty_clause(self):
        """Test rejection of empty clause"""
        is_valid, msg = validate_where_clause("")
        assert not is_valid
        assert "empty" in msg.lower()
    
    def test_reject_whitespace_only(self):
        """Test rejection of whitespace-only clause"""
        is_valid, msg = validate_where_clause("   ")
        assert not is_valid
    
    def test_case_insensitive_keywords(self):
        """Test that dangerous keywords are caught regardless of case"""
        clause = "title ILIKE '%test%'; DeLeTe FROM books"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    # ==================== FUZZY MATCHING TESTS (TYPOS) ====================
    
    def test_reject_delect_typo(self):
        """Test rejection of 'delect' typo for 'DELETE'"""
        clause = "delect all book releted education"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "delect" in msg.lower() or "delete" in msg.lower()
    
    def test_reject_delet_typo(self):
        """Test rejection of 'delet' typo for 'DELETE'"""
        clause = "delet FROM books WHERE title ILIKE '%test%'"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
        assert "delet" in msg.lower() or "delete" in msg.lower()
    
    def test_reject_updat_typo(self):
        """Test rejection of 'updat' typo for 'UPDATE'"""
        clause = "updat books SET price=0"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_reject_drp_typo(self):
        """Test rejection of 'drp' typo for 'DROP'"""
        clause = "drp TABLE books"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_reject_insrt_typo(self):
        """Test rejection of 'insrt' typo for 'INSERT'"""
        clause = "insrt INTO books VALUES (...)"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_reject_deleted_variation(self):
        """Test rejection of 'deleted' variation of 'DELETE'"""
        clause = "deleted FROM books"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_reject_deletes_variation(self):
        """Test rejection of 'deletes' variation of 'DELETE'"""
        clause = "deletes all records"
        is_valid, msg = validate_where_clause(clause)
        assert not is_valid
    
    def test_accept_select_safe_word(self):
        """Test that EXTRACT with SELECT is still allowed (it's a safe pattern)"""
        clause = "EXTRACT(YEAR FROM published_date) = 2020"
        is_valid, msg = validate_where_clause(clause)
        assert is_valid, f"Should be valid: {msg}"


class TestSQLWhereValidatorSanitization:
    """Test value sanitization"""
    
    def test_sanitize_simple_value(self):
        """Test sanitization of simple values"""
        result = SQLWhereValidator.sanitize_value("test")
        assert result == "'test'"
    
    def test_sanitize_escapes_quotes(self):
        """Test that single quotes are escaped"""
        result = SQLWhereValidator.sanitize_value("O'Reilly")
        assert result == "'O''Reilly'"
    
    def test_sanitize_multiple_quotes(self):
        """Test sanitization with multiple quotes"""
        result = SQLWhereValidator.sanitize_value("It's a 'test'")
        assert result == "'It''s a ''test'''"
