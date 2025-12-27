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
    # In a container, /nix/store is usually part of the image, but we need the DB to be valid.
    # dockerTools.buildImage doesn't fully initialize the runtime DB state.
    if [ ! -d /nix/var/nix/db ]; then
        echo "Initializing Nix DB..."
        mkdir -p /nix/var/nix
        ${pkgs.nix}/bin/nix-store --init
    fi

    # Fix permissions if needed (container might start as root then drop, 
    # but we are running as root to start sshd, so we can fix things)
    chown -R ${builderUser}:${builderUser} ${builderHome}
    
    # Allow the builder user to write to the nix store
    # In single-user mode, the running user needs write access.
    # Since we run sshd as root, the session will switch to 'nix' user.
    # We must ensure 'nix' owns /nix (or at least the parts it needs).
    # This is drastic but necessary for a single-user-like container setup
    # where the user isn't root but needs to install things.
    # Alternatively, we could configure 'nix' to rely on a daemon, 
    # but running the daemon inside the same container is complex.
    # Simpler: Make /nix owned by the builder user.
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

in pkgs.dockerTools.buildImage {
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

  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [
      pkgs.bashInteractive
      pkgs.coreutils
      pkgs.openssh
      pkgs.nix
      pkgs.cacert
      pkgs.git
      pkgs.iana-etc # /etc/protocols etc.
      
      (pkgs.runCommand "etc-setup" {} ''
        mkdir -p $out/etc/nix $out/etc/ssh $out/run $out/tmp
        ln -s ${nixConf} $out/etc/nix/nix.conf
        echo "root:x:0:0::/root:/bin/bash" > $out/etc/passwd
        echo "${builderUser}:x:${toString builderUid}:${toString builderUid}::${builderHome}:/bin/bash" >> $out/etc/passwd
        echo "root:x:0:" > $out/etc/group
        echo "${builderUser}:x:${toString builderUid}:" >> $out/etc/group
      '')
    ];
    pathsToLink = [ "/bin" "/etc" "/var" "/tmp" "/run" ];
  };

  runAsRoot = ''
    mkdir -p /home/${builderUser}
    chown ${toString builderUid}:${toString builderUid} /home/${builderUser}
    mkdir -p /tmp
    chmod 1777 /tmp
  '';
}
