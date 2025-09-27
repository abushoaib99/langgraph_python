import json

from typing import Any, Optional, TypedDict

from langgraph.constants import START
from langgraph.graph import StateGraph, END

from form_fillup.form_schema import schema
from form_fillup.model import llm


# Define the state structure for the workflow
class FormFillingState(TypedDict):
    """State object that gets passed between nodes in the workflow"""
    form_schema: dict[str, Any]
    user_context: str
    success: bool
    extracted_data: Optional[dict[str, Any]]
    missing_required_fields: Optional[list[str]]


class FormAutomationWorkflow:
    def __init__(self):
        """
        Initialize the form automation workflow
        """
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        # Create the state graph
        workflow = StateGraph(FormFillingState)

        # Add nodes
        workflow.add_node("validate_inputs", self._validate_inputs)
        workflow.add_node("extract_data", self._extract_data)
        workflow.add_node("check_required", self._check_required)
        workflow.add_node("ask_missing", self._ask_missing)

        # Add edges
        workflow.add_edge(START, "validate_inputs")
        workflow.add_edge("validate_inputs", "extract_data")
        workflow.add_edge("extract_data", "check_required")
        workflow.add_edge("check_required", "ask_missing")
        workflow.add_edge("ask_missing", END)

        return workflow.compile()

    def _validate_inputs(self, state: FormFillingState) -> FormFillingState:
        """Validate that we have the required inputs"""
        if not state.get("form_schema"):
            raise ValueError("Form schema is required")
        if not state.get("user_context"):
            raise ValueError("User context is required")

        return state

    def _extract_data(self, state: FormFillingState) -> FormFillingState:
        """Extract data from user context using LLM"""

        form_schema = state["form_schema"]
        user_context = state["user_context"]

        # Create the prompt template
        system_prompt = """You are an intelligent form-filling assistant. Your task is to extract information from natural language text and map it to the provided form structure.

INSTRUCTIONS:
1. Return ONLY a valid JSON object where keys are the 'id' of form fields
2. Values should be the extracted data from the user context
3. If a field cannot be filled from the context, omit it from the output
4. For 'select' type fields, choose the closest matching option from the provided options
5. For 'date' type fields, format as YYYY-MM-DD
6. For 'email' type fields, ensure proper email format
8. Be precise and don't make assumptions beyond what's clearly stated in the context

Return only the JSON object with extracted data:"""

        user_prompt = f"""
Form schema:
{json.dumps(form_schema, indent=2)}

User context:
\"{user_context}\"
"""

        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = llm.invoke(
                input=prompt,
                response_format={"type": "json_object"}
            )

            content = f"{response.content}".replace("```json", '').replace("```", '')

            # Parse the JSON response
            extracted_data = json.loads(content.strip())
            state["extracted_data"] = extracted_data
            state["success"] = True

        except json.JSONDecodeError as e:
            state["validation_errors"] = [f"Invalid JSON response from LLM: {str(e)}"]
        except Exception as e:
            state["validation_errors"] = [f"Error during extraction: {str(e)}"]

        return state

    def _check_required(self, state: FormFillingState) -> FormFillingState:
        extracted_data = state["extracted_data"]
        form_schema = state["form_schema"]
        missing = []

        for field in form_schema:
            fid = field["id"]
            if (field.get("required")) and (not extracted_data.get(fid)):
                missing.append({"id": fid, "label": field["label"]})

        state["missing_required_fields"] = missing
        return state

    def _ask_missing(self, state: FormFillingState) -> FormFillingState:
        missing = state.get("missing_required_fields", [])
        if missing:
            print("The following required fields are missing:")

            for f in missing:
                value = input(f"Enter value for '{f['label']}': ")
                state["extracted_data"][f["id"]] = value
        return state

    def process_form(self, form_schema: dict[str, Any], user_context: str) -> dict[str, Any]:
        """
        Main method to process form filling request

        Args:
            form_schema: Dictionary containing form structure
            user_context: Natural language text with information to extract
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary with extraction results
        """
        initial_state = FormFillingState(
            form_schema=form_schema,
            user_context=user_context,
            extracted_data=None
        )

        # Run the workflow
        result = self.workflow.invoke(initial_state)

        # Return appropriate response
        if result.get("extracted_data"):
            return result["extracted_data"]
        else:
            return {
                "success": False,
                "error": result.get("validation_errors", ["Unknown error occurred"]),
                "extracted_data": result.get("extracted_data", {})
            }


# Example usage and testing
def example_usage():
    """Example of how to use the FormAutomationWorkflow"""

    # Initialize the workflow
    workflow = FormAutomationWorkflow()

    with open("form_fillup.mmd", "w") as f:
        f.write(workflow.workflow.get_graph().draw_mermaid())

    # Example user context
    user_context = """Set up a new Capex. Want to buy a Laptop, Estimated amount 120000. For Develompent purpose.
    If buy a new laptop then development speed will be faster. Without the laptop current activities is hampering. No alternative purchase.
    He mentioned he needs priority support. Need urgent basis.
    Unit Name: Innoweb
    Date: Current Date
    For: Abu Souyeb
    Designation: Software Engineer
    """

    # Process the form
    result = workflow.process_form(schema, user_context)

    print("Form Filling Result:")
    print(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    # Run the example
    example_usage()
