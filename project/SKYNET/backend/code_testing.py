import ast
import sys
import io
import time
import traceback
import unittest
import tempfile
import os
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from contextlib import redirect_stdout, redirect_stderr
import json
import psutil
import asyncio
from dataclasses import dataclass

@dataclass
class TestResult:
    test_name: str
    passed: bool
    error_message: Optional[str]
    execution_time: float
    
@dataclass
class PerformanceMetrics:
    execution_time: float
    memory_usage: float  # in MB
    cpu_usage: float  # percentage
    complexity_score: int

class CodeAnalyzer:
    """Analyzes Python code for quality, performance, and generates unit tests"""
    
    @staticmethod
    def analyze_code(code: str) -> Dict[str, Any]:
        """Analyze code structure and quality"""
        try:
            tree = ast.parse(code)
            
            analysis = {
                "functions": [],
                "classes": [],
                "imports": [],
                "variables": [],
                "complexity": 0,
                "lines_of_code": len(code.split('\n')),
                "issues": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "returns": ast.unparse(node.returns) if node.returns else None,
                        "docstring": ast.get_docstring(node),
                        "complexity": CodeAnalyzer._calculate_complexity(node)
                    }
                    analysis["functions"].append(func_info)
                    
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        "docstring": ast.get_docstring(node)
                    }
                    analysis["classes"].append(class_info)
                    
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                        
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        analysis["imports"].append(f"{module}.{alias.name}")
            
            # Check for common issues
            analysis["issues"] = CodeAnalyzer._check_common_issues(tree)
            analysis["complexity"] = CodeAnalyzer._calculate_total_complexity(tree)
            
            return analysis
            
        except SyntaxError as e:
            return {
                "error": f"Syntax Error: {str(e)}",
                "line": e.lineno,
                "offset": e.offset
            }
    
    @staticmethod
    def _calculate_complexity(node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a node"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
                
        return complexity
    
    @staticmethod
    def _calculate_total_complexity(tree: ast.AST) -> int:
        """Calculate total complexity of the code"""
        total = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total += CodeAnalyzer._calculate_complexity(node)
        return total if total > 0 else 1
    
    @staticmethod
    def _check_common_issues(tree: ast.AST) -> List[str]:
        """Check for common code issues"""
        issues = []
        
        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    issues.append(f"Missing docstring for {node.name}")
        
        # Check for too many arguments
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.args.args) > 5:
                    issues.append(f"Function {node.name} has too many arguments ({len(node.args.args)})")
        
        # Check for global variables
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                issues.append(f"Use of global variable")
                
        return issues

class UnitTestGenerator:
    """Generates unit tests automatically for Python code"""
    
    @staticmethod
    def generate_tests(code: str, analysis: Dict[str, Any], num_tests: int = 15) -> str:
        """Generate unit tests based on code analysis with configurable test count"""
        
        test_code = []
        test_code.append("import unittest")
        test_code.append("import sys")
        test_code.append("import io")
        test_code.append("from contextlib import redirect_stdout, redirect_stderr")
        test_code.append("")
        
        # Add imports from the original code
        for imp in analysis.get("imports", []):
            if not imp.startswith("_"):
                test_code.append(f"import {imp}")
        
        test_code.append("")
        test_code.append("# Auto-generated test code")
        test_code.append("")
        
        # Add the original code as a module
        test_code.append("# Original code to test")
        test_code.append("exec('''")
        test_code.append(code.replace("'''", "\\'\\'\\'"))
        test_code.append("''')")
        test_code.append("")
        
        # Cap total tests generated based on num_tests
        tests_generated = 0
        max_tests = num_tests
        
        # Generate test classes for each class in the code (limit to fit within num_tests)
        classes_to_test = analysis.get("classes", [])
        for class_info in classes_to_test:
            if tests_generated >= max_tests:
                break
                
            test_code.append(f"class Test{class_info['name']}(unittest.TestCase):")
            test_code.append(f"    \"\"\"Test cases for {class_info['name']}\"\"\"")
            test_code.append("")
            
            # Setup method
            test_code.append("    def setUp(self):")
            test_code.append(f"        self.instance = {class_info['name']}()")
            test_code.append("")
            
            # Generate test for each method (limited by remaining test budget)
            methods = [m for m in class_info.get("methods", []) if not m.startswith("_")]
            remaining_tests = max_tests - tests_generated
            for method in methods[:remaining_tests]:
                test_code.append(f"    def test_{method}(self):")
                test_code.append(f"        \"\"\"Test {method} method\"\"\"")
                test_code.append("        # TODO: Add test implementation")
                test_code.append(f"        self.assertIsNotNone(self.instance.{method})")
                test_code.append("")
                tests_generated += 1
                if tests_generated >= max_tests:
                    break
        
        # Generate test class for functions (only if we haven't exceeded budget)
        if analysis.get("functions") and tests_generated < max_tests:
            test_code.append("class TestFunctions(unittest.TestCase):")
            test_code.append("    \"\"\"Test cases for standalone functions\"\"\"")
            test_code.append("")
            
            # Generate tests for remaining budget
            functions_to_test = analysis.get("functions", [])
            remaining_budget = max_tests - tests_generated
            
            for func_info in functions_to_test:
                if tests_generated >= max_tests:
                    break
                func_name = func_info["name"]
                args = func_info["args"]
                
                test_code.append(f"    def test_{func_name}(self):")
                test_code.append(f"        \"\"\"Test {func_name} function\"\"\"")
                
                # Generate test cases based on function signature
                if len(args) == 0:
                    test_code.append(f"        result = {func_name}()")
                    test_code.append("        self.assertIsNotNone(result)")
                elif len(args) == 1:
                    # Generate tests for common types
                    test_code.append("        # Test with different input types")
                    test_code.append(f"        test_cases = [")
                    test_code.append("            (0, 'zero'),")
                    test_code.append("            (1, 'positive'),")
                    test_code.append("            (-1, 'negative'),")
                    test_code.append("            ('test', 'string'),")
                    test_code.append("            ([], 'empty_list'),")
                    test_code.append("            ([1, 2, 3], 'list'),")
                    test_code.append("        ]")
                    test_code.append("        ")
                    test_code.append("        for test_input, case_name in test_cases:")
                    test_code.append("            try:")
                    test_code.append(f"                result = {func_name}(test_input)")
                    test_code.append("                # Add specific assertions here")
                    test_code.append("            except Exception as e:")
                    test_code.append("                # Handle expected exceptions")
                    test_code.append("                pass")
                else:
                    # Generate basic test with None values
                    args_str = ", ".join(["None"] * len(args))
                    test_code.append(f"        # Test with sample inputs")
                    test_code.append(f"        try:")
                    test_code.append(f"            result = {func_name}({args_str})")
                    test_code.append(f"        except:")
                    test_code.append(f"            # Function may require specific input types")
                    test_code.append(f"            pass")
                
                test_code.append("")
                tests_generated += 1
        
        # Add main execution
        test_code.append("if __name__ == '__main__':")
        test_code.append("    unittest.main()")
        
        return "\n".join(test_code)
    
    @staticmethod
    def generate_edge_case_tests(func_info: Dict[str, Any]) -> List[str]:
        """Generate edge case tests for a function"""
        tests = []
        func_name = func_info["name"]
        
        # Edge cases based on function name patterns
        if "sort" in func_name.lower():
            tests.append(f"self.assertEqual({func_name}([]), [])")
            tests.append(f"self.assertEqual({func_name}([1]), [1])")
            tests.append(f"self.assertEqual({func_name}([3, 1, 2]), [1, 2, 3])")
            
        elif "search" in func_name.lower() or "find" in func_name.lower():
            tests.append(f"self.assertIsNone({func_name}([], 1))")
            tests.append(f"self.assertEqual({func_name}([1, 2, 3], 2), 1)")
            
        elif "validate" in func_name.lower() or "check" in func_name.lower():
            tests.append(f"self.assertFalse({func_name}(None))")
            tests.append(f"self.assertFalse({func_name}(''))")
            
        return tests

class CodeExecutor:
    """Executes Python code safely and measures performance"""
    
    @staticmethod
    async def execute_code(code: str, timeout: int = 10) -> Dict[str, Any]:
        """Execute Python code with timeout and resource monitoring"""
        
        result = {
            "output": "",
            "error": None,
            "execution_time": 0,
            "memory_usage": 0,
            "cpu_usage": 0,
            "test_results": []
        }
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Execute the code with timeout
            start_time = time.time()
            
            proc = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                execution_time = time.time() - start_time
                
                # Get final memory usage
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = final_memory - initial_memory
                
                result["output"] = stdout
                result["error"] = stderr if stderr else None
                result["execution_time"] = execution_time
                result["memory_usage"] = max(0, memory_usage)
                result["success"] = proc.returncode == 0
                
            except subprocess.TimeoutExpired:
                proc.kill()
                result["error"] = f"Execution timeout ({timeout} seconds)"
                result["success"] = False
                
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return result
    
    @staticmethod
    async def run_tests(test_code: str) -> List[TestResult]:
        """Run unit tests and return results"""
        
        test_results = []
        
        # Create temporary file for test code
        with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        try:
            # Run the tests directly using the test file
            proc = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = proc.communicate(timeout=30)
            
            # Parse test results from stdout and stderr
            output = stdout + stderr
            
            # Check for test execution patterns
            if "Ran " in output:
                # Extract test count
                import re
                match = re.search(r'Ran (\d+) tests?', output)
                if match:
                    total_tests = int(match.group(1))
                    
                    # Check for failures
                    if "FAILED" in output or "ERROR" in output:
                        failed_match = re.search(r'FAILED \(.*?failures=(\d+).*?\)', output)
                        error_match = re.search(r'FAILED \(.*?errors=(\d+).*?\)', output)
                        
                        failures = int(failed_match.group(1)) if failed_match else 0
                        errors = int(error_match.group(1)) if error_match else 0
                        failed_count = failures + errors
                        passed_count = total_tests - failed_count
                        
                        # Add passed tests
                        for i in range(passed_count):
                            test_results.append(TestResult(
                                test_name=f"Test_{i+1}",
                                passed=True,
                                error_message=None,
                                execution_time=0
                            ))
                        
                        # Add failed tests
                        for i in range(failed_count):
                            test_results.append(TestResult(
                                test_name=f"Test_{passed_count+i+1}",
                                passed=False,
                                error_message="Test failed - check implementation",
                                execution_time=0
                            ))
                    elif "OK" in output:
                        # All tests passed
                        for i in range(total_tests):
                            test_results.append(TestResult(
                                test_name=f"Test_{i+1}",
                                passed=True,
                                error_message=None,
                                execution_time=0
                            ))
                else:
                    # Couldn't parse test count
                    test_results.append(TestResult(
                        test_name="Test Execution",
                        passed=False,
                        error_message="Could not parse test results",
                        execution_time=0
                    ))
            else:
                # No tests were run or error in test file
                test_results.append(TestResult(
                    test_name="Test Execution",
                    passed=False,
                    error_message=output if output else "No tests were executed",
                    execution_time=0
                ))
                        
        except subprocess.TimeoutExpired:
            test_results.append(TestResult(
                test_name="Test Execution",
                passed=False,
                error_message="Test execution timed out (30 seconds)",
                execution_time=0
            ))
        except Exception as e:
            test_results.append(TestResult(
                test_name="Test Execution",
                passed=False,
                error_message=str(e),
                execution_time=0
            ))
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # If no test results were generated, add a default failure
        if not test_results:
            test_results.append(TestResult(
                test_name="Test Execution",
                passed=False,
                error_message="No test results available",
                execution_time=0
            ))
        
        return test_results

class CodeProfiler:
    """Profile code performance and identify bottlenecks"""
    
    @staticmethod
    async def profile_code(code: str) -> Dict[str, Any]:
        """Profile code execution and identify performance issues"""
        
        profile_result = {
            "hotspots": [],
            "memory_leaks": [],
            "optimization_suggestions": [],
            "performance_score": 0
        }
        
        # Analyze code structure for performance issues
        try:
            tree = ast.parse(code)
            
            # Check for nested loops (O(n²) or worse)
            for node in ast.walk(tree):
                if isinstance(node, ast.For):
                    for child in ast.walk(node):
                        if child != node and isinstance(child, ast.For):
                            profile_result["hotspots"].append({
                                "type": "nested_loop",
                                "line": node.lineno,
                                "severity": "high",
                                "suggestion": "Consider using more efficient algorithms or data structures"
                            })
            
            # Check for inefficient operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id'):
                        func_name = node.func.id
                        if func_name in ['append', 'extend'] and isinstance(node, ast.For):
                            profile_result["optimization_suggestions"].append(
                                "Consider using list comprehension instead of append in loops"
                            )
            
            # Calculate performance score (0-100)
            score = 100
            score -= len(profile_result["hotspots"]) * 10
            score -= len(profile_result["optimization_suggestions"]) * 5
            profile_result["performance_score"] = max(0, score)
            
        except Exception as e:
            profile_result["error"] = str(e)
        
        return profile_result

class IntegrityChecker:
    """Check code integrity and security"""
    
    @staticmethod
    def check_integrity(code: str) -> Dict[str, Any]:
        """Check code for security issues and integrity problems"""
        
        issues = {
            "security_issues": [],
            "integrity_issues": [],
            "best_practice_violations": []
        }
        
        try:
            tree = ast.parse(code)
            
            # Check for eval/exec usage
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id') and node.func.id in ['eval', 'exec']:
                        issues["security_issues"].append({
                            "type": "dangerous_function",
                            "function": node.func.id,
                            "line": node.lineno,
                            "severity": "critical",
                            "message": f"Use of {node.func.id} is dangerous and should be avoided"
                        })
            
            # Check for hardcoded credentials
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if hasattr(target, 'id'):
                            var_name = target.id.lower()
                            if any(keyword in var_name for keyword in ['password', 'secret', 'api_key', 'token']):
                                if isinstance(node.value, ast.Constant):
                                    issues["security_issues"].append({
                                        "type": "hardcoded_credential",
                                        "variable": target.id,
                                        "line": node.lineno,
                                        "severity": "high",
                                        "message": "Hardcoded credentials detected"
                                    })
            
            # Check for SQL injection vulnerabilities
            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                    if isinstance(node.left, ast.Constant):
                        query = node.left.value
                        if isinstance(query, str) and any(sql in query.upper() for sql in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                            issues["security_issues"].append({
                                "type": "sql_injection_risk",
                                "line": node.lineno,
                                "severity": "high",
                                "message": "Potential SQL injection vulnerability"
                            })
            
        except Exception as e:
            issues["error"] = str(e)
        
        return issues