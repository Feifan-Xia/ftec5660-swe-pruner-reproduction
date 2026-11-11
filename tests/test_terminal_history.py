import types,unittest
from revision_full.fix_terminal_history import visible_observation_text
class TerminalHistoryTests(unittest.TestCase):
    def test_empty_inherited_content_preserves_actual_display(self):
        o=types.SimpleNamespace(content=[],output='visible code',to_llm_content=[types.SimpleNamespace(text='Raw Output: \nvisible code')])
        self.assertEqual(visible_observation_text(o),'Raw Output: \nvisible code')
    def test_pruned_raw_text_never_enters_summary(self):
        o=types.SimpleNamespace(content=[],output='kept line',original_output='kept line\nSECRET_REMOVED',to_llm_content=[types.SimpleNamespace(text='Filtered output: kept line')])
        self.assertEqual(visible_observation_text(o),'Filtered output: kept line')
        self.assertNotIn('SECRET_REMOVED',visible_observation_text(o))
    def test_recovery_metadata_and_tool_error_remain_visible(self):
        o=types.SimpleNamespace(to_llm_content=[types.SimpleNamespace(text='kept'),types.SimpleNamespace(text='saved obs_123, 3 lines')])
        self.assertEqual(visible_observation_text(o),'kept\nsaved obs_123, 3 lines')
        self.assertEqual(visible_observation_text(types.SimpleNamespace(message='range error',content=[])),'range error')
if __name__=='__main__':unittest.main()
