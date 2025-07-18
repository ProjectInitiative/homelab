storage "file" {
  path = "/openbao/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}

seal "pkcs11" {
  # This is the correct path inside the Ubuntu container.
  lib           = "/usr/lib/libtpm2_pkcs11.so"
  token_label   = "openbao-token"
  key_label     = "openbao-unseal-key"
  # You need to provide the PIN for OpenBao to use.
  pin           = "1234"

  # rsa_oaep_hash = "sha1"
  # CKM_AES_KEY_WRAP_PAD is a standard mechanism for wrapping keys with AES.
  # This tells OpenBao how to use the secret key.
  mechanism     = "0x210A"
}
