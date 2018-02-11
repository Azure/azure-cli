def create_managementpartner(client, managementpartner_id):
    return client.create(managementpartner_id)

def get_managementpartner(client, managementpartner_id):
    return client.get(managementpartner_id)

def update_managementpartner(client, managementpartner_id):
    return client.update(managementpartner_id)

def delete_managementpartner(client, managementpartner_id):
    return client.delete(managementpartner_id)
