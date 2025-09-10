from contextvars import ContextVar

context_store = ContextVar("context_store", default=[])
sql_store = ContextVar("sql_store", default=[])

def add_to_context_store(chunks: list) -> None:
    print("add_to_context_store")
    print(chunks)
    list_store = context_store.get()
    new_list = list_store.copy()
    new_list.extend(chunks)
    context_store.set(new_list)

def add_to_sql_store(sql: list) -> None:
    print("add_to_sql_store")
    # print(sql)
    list_store = sql_store.get()
    print(list_store)
    new_list = list_store.copy()
    print(new_list)
    new_list.append(sql)
    sql_store.set(new_list)
    print(sql_store.get())
