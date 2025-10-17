from ragas.dataset_schema import SingleTurnSample 
from ragas.metrics import Faithfulness
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper

from src.utils import get_llm, get_vanna

llm = LangchainLLMWrapper(get_llm())
vanna = get_vanna()

async def evaluate_response(
    user_input: str, 
    response: str, 
    retrieved_contexts: list,
    sql_list: list
):  

    context = []
    if retrieved_contexts:
        for ctx in retrieved_contexts:
            context.append(ctx['page_content'])

    if sql_list:
        for sql in sql_list:
            context.append(vanna.run_sql(sql).to_markdown())

    llm = LangchainLLMWrapper(get_llm())
    scorer = Faithfulness(llm=llm)

    sample = SingleTurnSample(
        user_input=user_input,
        response=response,
        retrieved_contexts=context
    )

    return await scorer.single_turn_ascore(sample)