time python SpecGeneration/spec_generate.py --seedAPI get_device --seedSecOp put_device --critical_var arg --max_depth 10 --repo_name linux
time python SpecGeneration/spec_generate.py --seedAPI kmalloc --seedSecOp kfree --critical_var retval --max_depth 10 --repo_name linux
time python SpecGeneration/spec_generate.py --seedAPI device_initialize --seedSecOp put_device --critical_var arg --max_depth 10 --repo_name linux
time python SpecGeneration/spec_generate.py --seedAPI kstrdup --seedSecOp kfree --critical_var retval --max_depth 10 --repo_name linux
time python SpecGeneration/spec_generate.py --seedAPI try_module_get --seedSecOp module_put --critidcal_var arg --max_depth 10 --repo_name linux
time python SpecGeneration/spec_generate.py --seedAPI ERR_PTR --seedSecOp IS_ERR --critical_var retval --max_depth 10 --repo_name linux