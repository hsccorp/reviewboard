from reviewboard.testing import TestCase
            self.assertTrue(file.origFile.startswith("%s/orig_src/" %
            self.assertTrue(file.newFile.startswith("%s/new_src/" %
    fixtures = ['test_scmtools']
            'diff --git a/README b/README\n'
            'index d6613f5..5b50866 100644\n'
            '--- README\n'
            '+++ README\n'
            'diff --git a/README b/README\n'
            'index d6613f5..5b50866 100644\n'
            '--- README\n'
            '+++ README\n'
        repository = self.create_repository(tool_name='Test')
    fixtures = ['test_scmtools']
        repository = self.create_repository()
        repository = self.create_repository()
            'diff --git a/README b/README\n'
            'index d6613f5..5b50866 100644\n'
            '--- README\n'
            '+++ README\n'
        repository = self.create_repository(tool_name='Test')
            'diff --git a/README b/README\n'
            'index d6613f5..5b50866 100644\n'
            '--- README\n'
            '+++ README\n'
        repository = self.create_repository(tool_name='Test')
            'diff --git a/README b/README\n'
            'index d6613f5..5b50866 100644\n'
            '--- README\n'
            '+++ README\n'
            'diff --git a/README b/README\n'
            'index d6613f4..5b50865 100644\n'
            '--- README\n'
            '+++ README\n'
            'diff --git a/UNUSED b/UNUSED\n'
            'index 1234567..5b50866 100644\n'
            '--- UNUSED\n'
            '+++ UNUSED\n'
        repository = self.create_repository(tool_name='Test')
        self.assertTrue(('/README', 'd6613f4') in saw_file_exists)
        self.assertFalse(('/UNUSED', '1234567') in saw_file_exists)