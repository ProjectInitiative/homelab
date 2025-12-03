self: super: {
  cdk8s-cli = super.cdk8s-cli.overrideAttrs (oldAttrs: {
    patches = (oldAttrs.patches or []) ++ [
      ./cleanup-permissions.patch
    ];
  });
}