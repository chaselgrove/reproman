# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the reproman package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##


# NOTE: The singularity classes SingularitySession and PTYSingularitySession
# are tested in test_session.test_session_abstract_methods()

import os.path as op

import pytest

import logging
import re
from ..singularity import Singularity, SingularitySession
from ...cmd import Runner
from ...tests.utils import assert_in
from ...tests.skip import mark
from ...utils import swallow_logs


def test_singularity_resource_image_required():
    with pytest.raises(TypeError):
        Singularity(name='foo')


@mark.skipif_no_network
@mark.skipif_no_singularity
def test_singularity_resource_class(tmpdir):
    tmpdir = str(tmpdir)
    with swallow_logs(new_level=logging.DEBUG) as log:
        Runner(cwd=tmpdir).run(
            ['singularity', 'pull', '--name', 'img',
             'shub://truatpasteurdotfr/singularity-alpine'])

        image = op.join(tmpdir, 'img')
        # Test creating a new singularity container instance.
        resource = Singularity(name='foo', image=image)
        assert resource.name == 'foo'
        assert resource.image == image
        resource.connect()
        assert resource.id is None
        assert resource.status is None
        list(resource.create())
        assert resource.id.startswith('foo-')
        assert resource.status == 'running'

        # Test trying to create an already running instance.
        resource_duplicate = Singularity(name='foo', image=image)
        resource_duplicate.connect()
        assert resource_duplicate.id.startswith('foo-')
        assert resource_duplicate.status == 'running'
        list(resource_duplicate.create())
        assert_in("Resource 'foo' already exists.", log.lines)

        # Test retrieving instance info.
        info = resource.get_instance_info()
        assert info['name'] == 'foo'
        assert re.match(r'^\d+$', info['pid'])

        info["image"] = image

        # Test starting an instance.
        with pytest.raises(NotImplementedError):
            resource.start()

        # Test stopping an instance.
        with pytest.raises(NotImplementedError):
            resource.stop()

        # Test getting a resource session.
        session = resource.get_session()
        assert isinstance(session, SingularitySession)

        # Test deleting an instance.
        resource.delete()
        assert resource.id is None
        assert resource.status is None

        # Test retrieving info from a non-existent instance.
        info = resource.get_instance_info()
        assert info is None
