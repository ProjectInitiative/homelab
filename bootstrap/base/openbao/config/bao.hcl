storage "file" {
  path = "/openbao/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}

seal "pkcs11" {
  lib           = "/usr/lib/libsofthsm2.so"
  # lib           = "/usr/lib/libtpm2_pkcs11.so"
  token_label   = "openbao-token"
  key_label     = "openbao-unseal-key"
  # pin           = "1234"

  # Use the recommended OAEP padding with a modern hash.
  # SoftHSM is fully compatible with this.
  rsa_oaep_hash = "sha1"
}
