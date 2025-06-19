import unittest
import subprocess
import sys
import os

class TestMainExecution(unittest.TestCase):

    def test_main_script_runs(self):
        """
        Test if the main.py script runs without critical errors and produces some output.
        This is a basic integration test for the initial TaskMasterAgent flow.
        """
        main_script_path = ""
        try:
            import mycrews.qrew
            package_path = os.path.dirname(mycrews.qrew.__file__)
            main_script_path = os.path.join(package_path, "main.py")
        except ImportError:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            main_script_path = os.path.join(base_dir, "qrew", "main.py")

        if not os.path.exists(main_script_path):
            self.fail(f"main.py not found at expected path: {main_script_path}. "
                      "Ensure the path is correct relative to the test execution context.")

        stdout_content = ""
        stderr_content = ""
        try:
            env = os.environ.copy()
            process = subprocess.Popen(
                [sys.executable, main_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            stdout_content, stderr_content = process.communicate(timeout=120) # Increased timeout

            print("\n--- main.py STDOUT ---")
            print(stdout_content)
            print("--- main.py STDERR ---")
            print(stderr_content)
            print("----------------------")

            self.assertEqual(process.returncode, 0, f"main.py exited with error code {process.returncode}. Stderr:\n{stderr_content}")
            self.assertIn("Initializing Qrew System...", stdout_content, "Initialization message not found in stdout.")
            self.assertIn("Kicking off TaskMasterAgent", stdout_content, "TaskMaster kickoff message not found.")
            self.assertIn("TaskMasterAgent Processing Complete.", stdout_content, "TaskMaster completion message not found.")
            self.assertIn("Result/Project Brief:", stdout_content, "Result section not found in stdout.")

        except subprocess.TimeoutExpired:
            self.fail(f"main.py execution timed out after 120 seconds. Stdout:\n{stdout_content}\nStderr:\n{stderr_content}")
        except Exception as e:
            self.fail(f"Executing main.py failed with an unexpected error: {e}")

if __name__ == '__main__':
    unittest.main()
