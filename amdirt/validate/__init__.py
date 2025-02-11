from amdirt.validate.application import AMDirValidator
import warnings

import amdirt.configuration.configuration as config

def run_validation(
    dataset,
    schema,
    schema_check,
    local_json_schema,
    line_dup,
    columns,
    doi,
    multi_values,
    online_archive,
    remote,
    markdown,
    verbose,
):
    if local_json_schema:
        config.settings.update({"local_json_schema": local_json_schema})
        
    if not verbose:
        warnings.filterwarnings("ignore")
    v = AMDirValidator(schema, dataset)
    if schema_check and v.parsing_ok:
        v.validate_schema()
    if line_dup and v.parsing_ok:
        v.check_duplicate_rows()
    if columns and v.parsing_ok:
        v.check_columns()
    if doi and v.parsing_ok:
        v.check_duplicate_dois()
    if multi_values and v.parsing_ok: 
        v.check_multi_values(column_names=multi_values)
    if online_archive and v.parsing_ok:
        v.check_sample_accession(remote=remote)
    if markdown:
        v.to_markdown()
    else:
        v.to_rich()
