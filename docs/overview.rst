Overview
========

django-badger is a reusable Django app that supports badges, to track and
award achievements by your users. This can be used to help encourage certain
behaviors, recognize skills, or just generally celebrate members of your
community.

This app aims to provide features such as:

- Basic badges, managed by the site owner in code and via Django admin.
- Badge awards, triggered in response to signal-based events with code
  collected in per-app ``badges.py`` modules.
- Views and models that enable users to create their own badges and nominate
  each other for awards.
- Meta-badges, for which an award is automatically issued when a complete set
  of prerequisite badge awards have been collected.
- Progress tracking, for which an award is issued when a user metric reaches
  100% of some goal, or in response to some other custom logic.
- Activity streams of badge awards.

For more about the thinking behind this project, check out this essay:
`Why does Mozilla need a Badger?  <http://decafbad.com/2010/07/badger-article/>`_

If you want to federate or share badges, you should check out
the `Mozilla Open Badges <https://github.com/mozilla/openbadges>`_ project.

.. vim:set tw=78 ai fo+=n fo-=l ft=rst:
