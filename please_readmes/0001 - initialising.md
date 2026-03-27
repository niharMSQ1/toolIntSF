# Initialising — tool integrations & evidence flow

**Integration-specific guides** (configure routes, OAuth, collect, unified sync) are listed in **[0000 - integrations_index.md](0000%20-%20integrations_index.md)**.

---

## Context

hi, I am starting multiple tool integrations categorised as HRMS, IDP, ITSM, IAM, Asset management, Devtools (github, bitbucket etc).

I have shared some png images which is inside the folder `db_structure` which are structure of required tables which I need to work upon.

### Uniqueness and updates

- **`tool_integrations`** — The pair `(organization_id, tool_id)` is **unique**. There must never be two rows for the same org and tool; if credentials or config change, **update** the existing row (do not insert a second row).

- **`evidence`** — For a given `organization_id`, **`title` must be unique** across all rows for that org (the same title cannot appear twice for the same organization). When evidence is collected again for the same org and title, **update** the existing row (do not insert a duplicate).

In both tables above, the intended behaviour is **upsert-style**: match on the unique key and **only update** when the row already exists.

**Full replace on update** — When updating an existing row in either table, **clear or discard the previous payload entirely** first, then **write the new data as a full replacement**. Do not merge or patch over old fields; the new state must always be written as if the old row’s content were erased and replaced wholesale.

---

## Sample payload

```json
{
  "org_id": "019ce23e-66b9-71fa-8223-8d66f1925bd5",
  "user_id": "019ce23e-67e0-702e-957d-ab3af1f8a619",
  "tool_id": "019ce23d-c16d-7304-a8b5-3500e3cbadbc",
  "configuration_data": {
    "client_id": "1000.JX39AHRQ82RG0TSZUYJ1WSU99S7ULW",
    "client_secret": "4136fb0f1435598dd1428d3cc6e11a80ab030b0a40",
    "redirect_uri": "http://localhost:8006/hrms/zoho-people/callback",
    "region": "in"
  }
}
```

where `configuration_data` will vary from tools to toosl

---

## Flow

**step 1** — when the user selects a tool from UI and enters credentials to start evidence collection.

**step 2** — the credentials are first saved in `tool_integrations` table.

**step 3** — Resolve the tool's **`domain_id`** from **`tools`** (`tools.domain_id`). **`evidence_masters`** is scoped by **`domain_id`** (and by integration **`source`**, e.g. `zoho_people`). Use the masters for that domain to know which evidence to collect; the **`name`** on each master still drives **`evidence.title`** (e.g. `employee directory`).

**step 4** — eviednce is collected from the tool apis and then a record is created in the `evidence` table and then the collection is saved in `evidence_collection` table

---

## step 5 — `evidence_mappeds`

we need to map the evidence with the controls in `evidence_mappeds` table. I need to explain how —

- **step 1 of step 5** — `evidence_id` in `evidence_mappeds` table is the id of the evidence which just created

- **step 2 of step 5** — `evidenceable_type` column value will be always saved as `App\Models\Control`

- **step 3 of step 5** — `evidenceable_id` is the control id which is associated with the evidence, Now I am sure here comes the confusion how.  
  the evidence is created from api whose "name" is defined in `evidence_masters` table,  
  so the primary key of that name is assocaited with 1 or more controls in `control_evidence_master` table.  
  So in `evidence_mappeds` we need to map the primary key of the object in `evidence_masters` with the controls, the relationship is one to many.
