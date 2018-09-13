"salt-call pillar.items --out=yaml > /tmp/pillar-post-engulf.yml":
  cmd.run

# TODO: this doesn't actually quite work yet:
# - There's some things we need to ignore ("configuration_init: default-import")
# - Sometimes the node roles seem to be listed in a different order (mon before
#   mgr or vice versa)
# - Engulf doesn't know about e.g.: the openattic role, so this will be missing
#   from the engulfed pillar data and the diff will fail
"diff -u /tmp/pillar-pre-engulf.yml /tmp/pillar-post-engulf.yml":
  cmd.run
