from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from djblets.util.misc import cache_memoize
from kgb import SpyAgency
from reviewboard.diffviewer.chunk_generator import DiffChunkGenerator
from reviewboard.diffviewer.errors import UserVisibleError
from reviewboard.diffviewer.forms import UploadDiffForm
from reviewboard.diffviewer.models import DiffSet, FileDiff
from reviewboard.diffviewer.myersdiff import MyersDiffer
from reviewboard.diffviewer.opcode_generator import get_diff_opcode_generator
from reviewboard.diffviewer.renderers import DiffRenderer
from reviewboard.diffviewer.templatetags.difftags import highlightregion
from reviewboard.scmtools.models import Repository, Tool
                         [("equal", 0, 3, 0, 3), ])
                         [("delete", 0, 3, 0, 0), ])
        opcodes = list(MyersDiffer(a, b).get_opcodes())
        differ = MyersDiffer(a, b)
        differ.add_interesting_lines_for_headers(filename)
        differ = MyersDiffer(old.splitlines(), new.splitlines())
        opcode_generator = get_diff_opcode_generator(differ)

        for opcodes in opcode_generator:
    PREFIX = os.path.join(os.path.dirname(__file__), 'testdata')
    def test_long_filenames(self):

    def test_diff_hashes(self):
        """
        Testing that uploading two of the same diff will result in only
        one database entry.
        """
        repository = Repository.objects.get(pk=1)
        diffset = DiffSet.objects.create(name='test',
                                         revision=1,
                                         repository=repository)
        f = open(os.path.join(self.PREFIX, "diffs", "context", "foo.c.diff"),
                 "r")
        data = f.read()
        f.close()

        filediff1 = FileDiff(diff=data,
                             diffset=diffset)
        filediff1.save()
        filediff2 = FileDiff(diff=data,
                             diffset=diffset)
        filediff2.save()

        self.assertEquals(filediff1.diff_hash, filediff2.diff_hash)


class DiffSetManagerTests(SpyAgency, TestCase):
    """Unit tests for DiffSetManager."""
    fixtures = ['test_scmtools']

    def test_creating_with_diff_data(self):
        """Test creating a DiffSet from diff file data"""
        diff = (
            'Index: README\n'
            '==========================================================='
            '========\n'
            '--- README  (revision 123)\n'
            '+++ README  (new)\n'
            '@ -1,1 +1,1 @@\n'
            '-blah..\n'
            '+blah blah\n'
        )

        repository = Repository.objects.create(
            name='Subversion SVN',
            path='file://%s' % (os.path.join(os.path.dirname(__file__),
                                             '..', 'scmtools', 'testdata',
                                             'svn_repo')),
            tool=Tool.objects.get(name='Subversion'))

        self.spy_on(repository.get_file_exists,
                    call_fake=lambda self, filename, revision, request: True)

        diffset = DiffSet.objects.create_from_data(
            repository, 'diff', diff, None, None, None, '/', None)

        self.assertEqual(diffset.files.count(), 1)


class UploadDiffFormTests(SpyAgency, TestCase):
    """Unit tests for UploadDiffForm."""
    fixtures = ['test_scmtools']

    def test_creating_diffsets(self):
        """Test creating a DiffSet from form data"""
        diff = (
            'Index: README\n'
            '==========================================================='
            '========\n'
            '--- README  (revision 123)\n'
            '+++ README  (new)\n'
            '@ -1,1 +1,1 @@\n'
            '-blah..\n'
            '+blah blah\n'
        )

        diff_file = SimpleUploadedFile('diff', diff,
                                       content_type='text/x-patch')

        repository = Repository.objects.create(
            name='Subversion SVN',
            path='file://%s' % (os.path.join(os.path.dirname(__file__),
                                             '..', 'scmtools', 'testdata',
                                             'svn_repo')),
            tool=Tool.objects.get(name='Subversion'))

        self.spy_on(repository.get_file_exists,
                    call_fake=lambda self, filename, revision, request: True)

        form = UploadDiffForm(
            repository=repository,
            data={
                'basedir': '/',
                'base_commit_id': '1234',
            },
            files={
                'path': diff_file,
            })
        self.assertTrue(form.is_valid())

        diffset = form.create(diff_file)
        self.assertEqual(diffset.files.count(), 1)
        self.assertEqual(diffset.basedir, '/')
        self.assertEqual(diffset.base_commit_id, '1234')

    def test_parent_diff_filtering(self):
        """Testing UploadDiffForm and filtering parent diff files"""
        saw_file_exists = {}

        def get_file_exists(repository, filename, revision, request):
            saw_file_exists[(filename, revision)] = True
            return True

        diff = (
            'Index: README\n'
            '==========================================================='
            '========\n'
            '--- README  (revision 124)\n'
            '+++ README  (new)\n'
            '@ -1,1 +1,1 @@\n'
            '-blah blah\n'
            '+blah!\n'
        )
        parent_diff_1 = (
            'Index: README\n'
            '==========================================================='
            '========\n'
            '--- README  (revision 123)\n'
            '+++ README  (new)\n'
            '@ -1,1 +1,1 @@\n'
            '-blah..\n'
            '+blah blah\n'
        )
        parent_diff_2 = (
            'Index: UNUSED\n'
            '==========================================================='
            '========\n'
            '--- UNUSED  (revision 123)\n'
            '+++ UNUSED  (new)\n'
            '@ -1,1 +1,1 @@\n'
            '-foo\n'
            '+bar\n'
        )
        parent_diff = parent_diff_1 + parent_diff_2

        diff_file = SimpleUploadedFile('diff', diff,
                                       content_type='text/x-patch')
        parent_diff_file = SimpleUploadedFile('parent_diff', parent_diff,
                                              content_type='text/x-patch')

        # Note that we're using SVN here for the test just because it's
        # a bit easier to test with than Git (easier diff parsing logic
        # and revision numbers).
        repository = Repository.objects.create(
            name='Subversion SVN',
            path='file://%s' % (os.path.join(os.path.dirname(__file__),
                                             '..', 'scmtools', 'testdata',
                                             'svn_repo')),
            tool=Tool.objects.get(name='Subversion'))
        self.spy_on(repository.get_file_exists, call_fake=get_file_exists)

        form = UploadDiffForm(
            repository=repository,
            data={
                'basedir': '/',
            },
            files={
                'path': diff_file,
                'parent_diff_path': parent_diff_file,
            })
        self.assertTrue(form.is_valid())

        diffset = form.create(diff_file, parent_diff_file)
        self.assertEqual(diffset.files.count(), 1)

        filediff = diffset.files.get()
        self.assertEqual(filediff.diff, diff)
        self.assertEqual(filediff.parent_diff, parent_diff_1)

        self.assertTrue(('/README', '123') in saw_file_exists)
        self.assertFalse(('/UNUSED', '123') in saw_file_exists)
        self.assertEqual(len(saw_file_exists), 1)

    def test_mercurial_parent_diff_base_rev(self):
        """Testing that the correct base revision is used for Mercurial diffs"""
        diff = (
            '# Node ID a6fc203fee9091ff9739c9c00cd4a6694e023f48\n'
            '# Parent  7c4735ef51a7c665b5654f1a111ae430ce84ebbd\n'
            'diff --git a/doc/readme b/doc/readme\n'
            '--- a/doc/readme\n'
            '+++ b/doc/readme\n'
            '@@ -1,3 +1,3 @@\n'
            ' Hello\n'
            '-\n'
            '+...\n'
            ' goodbye\n'
        )

        parent_diff = (
            '# Node ID 7c4735ef51a7c665b5654f1a111ae430ce84ebbd\n'
            '# Parent  661e5dd3c4938ecbe8f77e2fdfa905d70485f94c\n'
            'diff --git a/doc/newfile b/doc/newfile\n'
            'new file mode 100644\n'
            '--- /dev/null\n'
            '+++ b/doc/newfile\n'
            '@@ -0,0 +1,1 @@\n'
            '+Lorem ipsum\n'
        )

        diff_file = SimpleUploadedFile('diff', diff,
                                       content_type='text/x-patch')
        parent_diff_file = SimpleUploadedFile('parent_diff', parent_diff,
                                              content_type='text/x-patch')

        repository = Repository.objects.create(
            name='Test HG',
            path='scmtools/testdata/hg_repo.bundle',
            tool=Tool.objects.get(name='Mercurial'))

        form = UploadDiffForm(
            repository=repository,
            files={
                'path': diff_file,
                'parent_diff_path': parent_diff_file,
            })
        self.assertTrue(form.is_valid())

        diffset = form.create(diff_file, parent_diff_file)
        self.assertEqual(diffset.files.count(), 1)

        filediff = diffset.files.get()

        self.assertEqual(filediff.source_revision,
                         '661e5dd3c4938ecbe8f77e2fdfa905d70485f94c')


class DiffChunkGeneratorTests(TestCase):
    """Unit tests for DiffChunkGenerator."""
    def test_get_line_changed_regions(self):
        """Testing DiffChunkGenerator._get_line_changed_regions"""
        def deep_equal(A, B):
            typea, typeb = type(A), type(B)
            self.assertEqual(typea, typeb)
            if typea is tuple or typea is list:
                for a, b in map(None, A, B):
                    deep_equal(a, b)
            else:
                self.assertEqual(A, B)

        filediff = FileDiff(source_file='foo', diffset=DiffSet())
        generator = DiffChunkGenerator(None, filediff)

        deep_equal(generator._get_line_changed_regions(None, None),
                   (None, None))

        old = 'submitter = models.ForeignKey(Person, verbose_name="Submitter")'
        new = 'submitter = models.ForeignKey(User, verbose_name="Submitter")'
        regions = generator._get_line_changed_regions(old, new)
        deep_equal(regions, ([(30, 36)], [(30, 34)]))

        old = '-from reviews.models import ReviewRequest, Person, Group'
        new = '+from .reviews.models import ReviewRequest, Group'
        regions = generator._get_line_changed_regions(old, new)
        deep_equal(regions, ([(0, 1), (6, 6), (43, 51)],
                             [(0, 1), (6, 7), (44, 44)]))

        old = 'abcdefghijklm'
        new = 'nopqrstuvwxyz'
        regions = generator._get_line_changed_regions(old, new)
        deep_equal(regions, (None, None))


class DiffRendererTests(SpyAgency, TestCase):
    """Unit tests for DiffRenderer."""
    def test_construction_with_invalid_chunks(self):
        """Testing DiffRenderer construction with invalid chunks"""
        diff_file = {
            'chunks': [{}]
        }

        self.assertRaises(
            UserVisibleError,
            lambda: DiffRenderer(diff_file, chunk_index=-1))
        self.assertRaises(
            UserVisibleError,
            lambda: DiffRenderer(diff_file, chunk_index=1))

    def test_construction_with_valid_chunks(self):
        """Testing DiffRenderer construction with valid chunks"""
        diff_file = {
            'chunks': [{}]
        }

        # Should not assert.
        renderer = DiffRenderer(diff_file, chunk_index=0)
        self.assertEqual(renderer.num_chunks, 1)
        self.assertEqual(renderer.chunk_index, 0)

    def test_render_to_response(self):
        """Testing DiffRenderer.render_to_response"""
        diff_file = {
            'chunks': [{}]
        }

        renderer = DiffRenderer(diff_file)
        self.spy_on(renderer.render_to_string, call_fake=lambda self: 'Foo')

        response = renderer.render_to_response()

        self.assertTrue(renderer.render_to_string.called)
        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEqual(response.content, 'Foo')

    def test_render_to_string(self):
        """Testing DiffRenderer.render_to_string"""
        diff_file = {
            'chunks': [{}]
        }

        renderer = DiffRenderer(diff_file)
        self.spy_on(renderer.render_to_string_uncached,
                    call_fake=lambda self: 'Foo')
        self.spy_on(renderer.make_cache_key,
                    call_fake=lambda self: 'my-cache-key')
        self.spy_on(cache_memoize)

        response = renderer.render_to_response()

        self.assertEqual(response.content, 'Foo')
        self.assertTrue(renderer.render_to_string_uncached.called)
        self.assertTrue(renderer.make_cache_key.called)
        self.assertTrue(cache_memoize.spy.called)

    def test_render_to_string_uncached(self):
        """Testing DiffRenderer.render_to_string_uncached"""
        diff_file = {
            'chunks': [{}]
        }

        renderer = DiffRenderer(diff_file, lines_of_context=[5, 5])
        self.spy_on(renderer.render_to_string_uncached,
                    call_fake=lambda self: 'Foo')
        self.spy_on(renderer.make_cache_key,
                    call_fake=lambda self: 'my-cache-key')
        self.spy_on(cache_memoize)

        response = renderer.render_to_response()

        self.assertEqual(response.content, 'Foo')
        self.assertTrue(renderer.render_to_string_uncached.called)
        self.assertFalse(renderer.make_cache_key.called)
        self.assertFalse(cache_memoize.spy.called)

    def test_make_context_with_chunk_index(self):
        """Testing DiffRenderer.make_context with chunk_index"""
        diff_file = {
            'chunks': [
                {
                    'lines': [],
                    'meta': {},
                    'change': 'insert',
                },
                {
                    # This is not how lines really look, but it's fine for
                    # current usage tests.
                    'lines': range(10),
                    'meta': {},
                    'change': 'replace',
                },
                {
                    'lines': [],
                    'meta': {},
                    'change': 'delete',
                }
            ],
        }

        renderer = DiffRenderer(diff_file, chunk_index=1)
        context = renderer.make_context()

        self.assertEqual(context['standalone'], True)
        self.assertEqual(context['file'], diff_file)
        self.assertEqual(len(diff_file['chunks']), 1)

        chunk = diff_file['chunks'][0]
        self.assertEqual(chunk['change'], 'replace')