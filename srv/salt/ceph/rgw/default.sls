
install rgw:
  pkg.installed:
    - name: ceph-radosgw

{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
start {{ config }}:
  service.running:
    - name: ceph-radosgw@{{ config }}
    - enable: True
    - require:
        - pkg: install rgw

{% endfor %}