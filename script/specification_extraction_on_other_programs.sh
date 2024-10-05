python spec_generate.py --seedAPI av_malloc --seedSecOp av_free --critical_var retval --max_depth 5 --repo_name FFmpeg
python spec_generate.py --seedAPI BIO_new --seedSecOp BIO_free --critical_var retval --max_depth 5 --repo_name openssl
