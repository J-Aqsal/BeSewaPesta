from django.db import connection


def dbFetch( # for collecting data from db
    query,
    params=None,
    fetchAll=False # if true, return list of rows, else return single row
):

    with connection.cursor() as cursor:

        cursor.execute(query, params or [])

        columns = [col[0] for col in cursor.description]

        if fetchAll:

            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

        row = cursor.fetchone()

        if not row:
            return None

        return dict(zip(columns, row))


def dbExecute( # for executing query that doesn't return data, like insert/update/delete
    query,
    params=None,
    returning=False # if true, return the row returned by the query (for insert with returning id)
):

    with connection.cursor() as cursor:

        cursor.execute(query, params or [])
        
        if returning:
            columns = [col[0] for col in cursor.description]

            row = cursor.fetchone()

            if not row:
                return None

            return dict(zip(columns, row))

