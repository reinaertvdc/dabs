wait_time = 2

ada = type('', (object,), {
    'scheme': 'http',
    'username': '',
    'password': '',
    'host': 'ada',
    'path': 'DocRoom/DM_DOCUMENTLIST.aspx',
    'query_string': 'DM_SCREEN_ID=111344&screenmode=query'
})()

dabs = type('', (object,), {
    'scheme': 'https',
    'username': '',
    'password': '',
    'host': 'csdabs.ciport.be',
    'path': 'csdabs/migrations/to-validate',
    'query_string': 'realm_uuid=cdcd0d62-3e10-4fbb-9a93-aa584bd91379'
})()
