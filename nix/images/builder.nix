{ pkgs }:

let
  builderUser = "nix";
  builderUid = 1000;
  builderHome = "/home/${builderUser}";

  sshdConfig = pkgs.writeText "sshd_config" ''
    Port 2222
    HostKey /etc/ssh/ssh_host_ed25519_key
    AuthorizedKeysFile /etc/ssh/authorized_keys
    PermitRootLogin no
    PasswordAuthentication no
    ChallengeResponseAuthentication no
    PrintMotd no
    PidFile /run/sshd.pid
    StrictModes no
  '';

  entrypoint = pkgs.writeShellScriptBin "entrypoint" ''
    set -e
    
    # Generate host keys if not present (fallback)
    if [ ! -f /etc/ssh/ssh_host_ed25519_key ]; then
      echo "Generating fallback host key..."
      ${pkgs.openssh}/bin/ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""
    fi

    # Ensure /nix/var/nix/db exists and is writable
    if [ ! -d /nix/var/nix/db ]; then
        echo "Initializing Nix DB..."
        mkdir -p /nix/var/nix
        ${pkgs.nix}/bin/nix-store --init
    fi

    # Fix permissions if needed
    chown -R ${builderUser}:${builderUser} ${builderHome}
    
    # Allow the builder user to write to the nix store
    chown -R ${builderUser}:${builderUser} /nix

    echo "Starting SSHD on port 2222..."
    ${pkgs.openssh}/bin/sshd -D -f ${sshdConfig} -E /dev/stderr
  '';

  nixConf = pkgs.writeText "nix.conf" ''
    sandbox = false
    trusted-users = root ${builderUser}
    experimental-features = nix-command flakes
    build-users-group = 
    extra-platforms = aarch64-linux
  '';

# Changed from buildImage to buildLayeredImage
in pkgs.dockerTools.buildLayeredImage {
  name = "nixos-remote-builder";
  tag = "latest";

  config = {
    Cmd = [ "${entrypoint}/bin/entrypoint" ];
    ExposedPorts = {
      "2222/tcp" = {};
    };
    Env = [
      "NIX_CONF_DIR=/etc/nix"
      "PATH=/bin:/usr/bin:${pkgs.nix}/bin"
      "USER=${builderUser}"
    ];
  };

  contents = [
    pkgs.bashInteractive
    pkgs.coreutils
    pkgs.openssh
    pkgs.nix
    pkgs.cacert
    pkgs.git
    pkgs.iana-etc
    
    (pkgs.runCommand "etc-setup" {} ''
      mkdir -p $out/etc/nix $out/etc/ssh $out/run $out/tmp
      ln -s ${nixConf} $out/etc/nix/nix.conf
      echo "root:x:0:0::/root:/bin/bash" > $out/etc/passwd
      echo "${builderUser}:x:${toString builderUid}:${toString builderUid}::${builderHome}:/bin/bash" >> $out/etc/passwd
      echo "root:x:0:" > $out/etc/group
      echo "${builderUser}:x:${toString builderUid}:" >> $out/etc/group
    '')
  ];

  # Corrected typo: fakeRootCommands
  # Paths must be relative (starting with ./) inside this block
  fakeRootCommands = ''
    mkdir -p ./home/${builderUser}
    chown ${toString builderUid}:${toString builderUid} ./home/${builderUser}
    mkdir -p ./tmp
    chmod 1777 ./tmp
  '';
}