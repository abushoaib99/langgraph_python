import json

from form_fillup.db_connection import get_db_connection

conn = get_db_connection()


def execute_query(query: str):
    """
    Execute a SQL query in PostgreSQL.
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchone()

        conn.commit()
        conn.close()

        if rows:
            return rows[0]
    except Exception as e:
        print(f"Error executing query: {e}")
        return None


def get_eform_variables(eform_id: int) -> list | None:
    """
    Inserts a new chatbot interaction into PostgreSQL.
    """

    query = f"""
        SELECT content from bpmn_eform
        WHERE id={eform_id}
        """

    content = execute_query(query=query)

    if not content:
        return None

    content = json.loads(content)
    items = content['items'][0]['items']

    response = []
    for row in items:
        for columns in row:
            if columns.get('variable'):
                if columns['type'] == 'grid':
                    grid_fields = []
                    for col in columns['columns']:
                        grid_fields.append({
                            'id': f"{columns['type']}-{columns['variable']}-{col['name']}",
                            'label': col['label'],
                        })
                    response.append({
                        'id': columns['id'],
                        'label': columns['label'],
                        'fields': grid_fields
                    })
                else:
                    response.append({
                        'id': f"checkgroup-{columns['id']}" if columns['type'] == 'checkgroup' else columns['id'],
                        'label': columns['label'],
                        'options': columns.get('options')
                    })

    return response

