from langchain_core.tools import tool
from pydantic import BaseModel, Field
from app.config import get_vector_store, get_vanna
from app.utils import add_to_context_store, add_to_sql_store

vector_store = get_vector_store()
vanna = get_vanna()

# Base Query schema
class Query(BaseModel):
    query: str = Field(..., description="The input query to the agent by the user")

# registry to hold all tools
REGISTERED_TOOLS = []

def auto_tool(args_schema):
    """Decorator that applies @tool and auto-registers the function in a global list."""

    def decorator(func):
        wrapped = tool(args_schema=args_schema)(func)  
        REGISTERED_TOOLS.append(wrapped)
        return wrapped

    return decorator

@auto_tool(args_schema=Query)
async def ask_about_credit_cards_fraud_theory(query: str) -> str:
    """Useful for retrieving information about credit card fraud theory.
    
    Example Question :
    - "What are the main types of credit card frauds?"
    - "What are the different methods used to commit credit card frauds?"
    - "What is the impact of credit card fraud on cardholders, merchants, issuers?"
    """
    context = vector_store.similarity_search(query, k=5)
    add_to_context_store(context)
    return f' context: {context}'

@auto_tool(args_schema=Query)
async def ask_about_credit_cards_fraud_database(query: str) -> str:
    """Useful for retrieving information about credit card fraud from the database.
    
    Example Question :
    - "What is the average transaction amount per month, and how does fraud percentage vary monthly?"
    - "Which ZIP codes show the highest fraud rates?"
    - "Do specific jobs appear more vulnerable to fraud?

    """
    sql = vanna.generate_sql(query, allow_llm_to_see_data=True)
    add_to_sql_store(sql)
    return vanna.run_sql(sql)