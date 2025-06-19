# mycrews/qrew/utils/reporting.py
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

class ErrorSummary:
    def __init__(self):
        self.records = []  # list of dicts: {stage, success, message, timestamp}

    def add(self, stage: str, success: bool, message: str = ""):
        # Truncate message to avoid long lines
        short_msg = (message[:200] + "...") if len(message) > 200 else message
        self.records.append({
            "stage": stage,
            "success": success,
            "message": short_msg,
            "timestamp": datetime.utcnow().isoformat()
        })

    def print(self): # This old print method will be superseded by RichProjectReporter
        print("\n\n=== Workflow Summary ===")
        print(f"{'Stage':<25} {'Status':<8} {'Details'}")
        print("-" * 60)
        for record in self.records:
            status = "✅" if record["success"] else "❌"
            print(f"{record['stage']:<25} {status:<8} {record['message']}")
        print("=" * 60)

    def to_dict(self):
        return self.records.copy()


class RichProjectReporter:
    def __init__(self, project_state: dict):
        self.state = project_state
        self.console = Console() # Each reporter instance can have its own console

    def _format_timestamp(self, ts_string):
        if not ts_string:
            return "N/A"
        try:
            dt_obj = datetime.fromisoformat(ts_string)
            return dt_obj.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError):
            return ts_string # Return original if parsing fails

    def print_report(self):
        project_name = self.state.get("project_name", "N/A Project Name")
        # Use Text.from_markup for title to allow direct Rich markup
        report_title_text = Text.from_markup(f"[bold cyan]Project Manager's Report for: {project_name}[/bold cyan]", justify="center")

        self.console.print() # Extra line for spacing
        self.console.print(Panel(report_title_text, title="[bold green]Qrew Project Summary[/bold green]", border_style="green", expand=False))
        self.console.print() # Extra line for spacing

        # Overall Status and Timestamps
        overall_status_str = self.state.get("status", "Unknown")
        # Handle "in_progress" from state for display
        display_status = "In Progress" if overall_status_str == "in_progress" else overall_status_str.capitalize()

        status_style = "yellow" # Default for In Progress / Unknown
        if overall_status_str == "completed":
            status_style = "green"
        elif overall_status_str == "failed":
            status_style = "red"

        created_at = self._format_timestamp(self.state.get("created_at"))
        updated_at = self._format_timestamp(self.state.get("updated_at"))
        completed_at = self._format_timestamp(self.state.get("completed_at")) # No default "N/A" here, handled by _format_timestamp

        overview_table = Table(show_header=False, box=None, padding=(0,1))
        overview_table.add_column(style="bold magenta", width=15) # Fixed width for labels
        overview_table.add_column()
        overview_table.add_row("Project Name:", project_name)
        overview_table.add_row("Overall Status:", Text(display_status, style=status_style))
        overview_table.add_row("Created At:", created_at)
        overview_table.add_row("Last Updated:", updated_at)
        if overall_status_str == "completed" and self.state.get("completed_at"):
            overview_table.add_row("Completed At:", completed_at)

        self.console.print(overview_table)
        self.console.print()

        # Stages Summary
        self.console.print(Text("--- Stage Summary ---", style="bold yellow", justify="center"))
        stages_table = Table(title=None, box=None, show_lines=False, padding=(0,1))
        stages_table.add_column("Stage", style="cyan", no_wrap=True, width=25)
        stages_table.add_column("Status", width=8, justify="center")
        stages_table.add_column("Details / Key Output")

        completed_stages = self.state.get("completed_stages", [])
        error_summary_records = self.state.get("error_summary", [])

        error_map = {record['stage']: record for record in error_summary_records}

        defined_stages = ["taskmaster", "architecture", "tech_vetting", "crew_assignment", "subagent_execution", "final_assembly", "project_finalization"]
        displayed_stages = set()

        for stage_name in defined_stages:
            # Display a stage if it was completed OR if it has an error record (even if not completed)
            if stage_name in completed_stages or stage_name in error_map:
                record = error_map.get(stage_name)
                # If completed but no specific error_map entry, assume success for completion status
                is_successful = (record and record["success"]) if record else (stage_name in completed_stages)

                status_icon = Text("✅", style="bright_green") if is_successful else Text("❌", style="bright_red")
                details = (record["message"] if record else "Completed") if is_successful else (record["message"] if record else "Failed - reason not recorded")

                stage_artifacts = self.state.get("artifacts", {}).get(stage_name, {})
                artifact_summary_parts = []
                if isinstance(stage_artifacts, dict):
                    if stage_name == "taskmaster" and "refined_brief" in stage_artifacts:
                        brief = stage_artifacts['refined_brief']
                        artifact_summary_parts.append(f"Brief: {brief[:70]}{'...' if len(brief) > 70 else ''}")
                    elif stage_name == "architecture" and "architecture_document_markdown" in stage_artifacts:
                        artifact_summary_parts.append("Architecture Doc: Generated")
                    elif stage_name == "final_assembly" and stage_artifacts.get("status") == "success_code_generation":
                        num_files = len(stage_artifacts.get("generated_files", [])) # Assuming generated_files is a list now
                        artifact_summary_parts.append(f"Generated {num_files} code file(s).")
                    elif stage_artifacts:
                        keys = [str(k) for k in stage_artifacts.keys() if k != 'error'] # Exclude common error key
                        if keys:
                            artifact_summary_parts.append(f"Outputs: {', '.join(keys[:2])}{'...' if len(keys) > 2 else ''}")

                if artifact_summary_parts:
                    details += f" ([italic]{'; '.join(artifact_summary_parts)}[/italic])"

                stages_table.add_row(stage_name.replace("_", " ").capitalize(), status_icon, Text.from_markup(details)) # Allow markup in details
                displayed_stages.add(stage_name)

        for stage_name, record in error_map.items():
            if stage_name not in displayed_stages: # Ad-hoc stages not in defined_stages but have errors
                status_icon = Text("❌", style="bright_red") # Must have failed if it's an error record not otherwise caught
                stages_table.add_row(stage_name.replace("_", " ").capitalize(), status_icon, Text.from_markup(record["message"]))

        if not stages_table.row_count: # Check if any rows were added
            self.console.print(Text("No stage information available.", style="italic yellow", justify="center"))
        else:
            self.console.print(stages_table)
        self.console.print()

        # Key Project Artifacts
        self.console.print(Text("--- Key Project Artifacts ---", style="bold yellow", justify="center"))
        final_assembly_artifacts = self.state.get("artifacts", {}).get("final_assembly", {})

        if final_assembly_artifacts.get("status") == "success_code_generation" and final_assembly_artifacts.get("generated_files"):
            # Assuming generated_files is a list of file paths/names
            generated_files_list = final_assembly_artifacts.get("generated_files", [])
            if isinstance(generated_files_list, dict): # Adapt if it's a dict {path: content}
                generated_files_list = list(generated_files_list.keys())

            if generated_files_list:
                files_table = Table(show_header=False, box=None, padding=(0,1))
                files_table.add_column("File Path", style="green")
                for file_path in generated_files_list[:5]:
                    files_table.add_row(str(file_path)) # Ensure path is string
                if len(generated_files_list) > 5:
                    files_table.add_row(f"...and {len(generated_files_list) - 5} more files.")
                self.console.print(files_table)
            else:
                self.console.print(Text("Code generation reported success, but no files listed.", style="italic yellow", justify="center"))

        else:
            arch_doc_md = self.state.get("artifacts",{}).get("architecture",{}).get("architecture_document_markdown","")
            if arch_doc_md and len(arch_doc_md) > 10 : # Check if markdown seems substantial
                self.console.print(Text("- Architecture Document: Available (markdown)", style="green"))
            else:
                self.console.print(Text("No specific final code artifacts listed. Check individual stage outputs.", style="italic yellow", justify="center"))
        self.console.print()

        # Error Summary section (only if project failed or has non-successful stage records)
        project_failed = self.state.get("status") == "failed"
        has_stage_errors = any(not r.get("success", True) for r in error_summary_records)

        if project_failed or has_stage_errors:
            self.console.print(Text("--- Error Details ---", style="bold red", justify="center"))
            error_table = Table(show_header=False, box=None, padding=(0,1))
            error_table.add_column("Stage", style="cyan", width=25)
            error_table.add_column("Message", style="red")

            found_errors_in_summary = False
            for record in error_summary_records:
                if not record.get("success", True): # If success is False or missing
                    error_table.add_row(record["stage"].replace("_", " ").capitalize(), record["message"])
                    found_errors_in_summary = True

            if not found_errors_in_summary and project_failed:
                 self.console.print(Text("Project status is 'failed', but no specific error messages were recorded in the summary.", style="italic yellow", justify="center"))
            elif found_errors_in_summary:
                 self.console.print(error_table)
            # If not project_failed and no stage_errors, this whole section is skipped.

        self.console.print(Panel(Text("End of Report", justify="center", style="dim white on rgb(30,30,30)"), border_style="dim"))
        self.console.print() # Final blank line
