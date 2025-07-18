storage "file" {
  path = "/openbao/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}

seal "pkcs11" {
  # This is the correct path inside the Ubuntu container.
  lib           = "/usr/lib/libsofthsm2.so"
  # lib           = "/usr/lib/libtpm2_pkcs11.so"
  token_label   = "openbao-token"
  key_label     = "openbao-unseal-key"
  key_id        = "6f70656e62616f2d756e7365616c"
  # You need to provide the PIN for OpenBao to use.
  pin           = "1234"

  # Use the recommended OAEP padding with a modern hash.
  # SoftHSM is fully compatible with this.
  rsa_oaep_hash = "sha256"
  # Explicitly set the mechanism to CKM_RSA_PKCS.
  # This is the most basic RSA padding scheme.
  mechanism     = "0x0001"
  
  # Use a more modern and robust hash algorithm.

  # rsa_oaep_hash = "sha1"
}
