"""Prepare a synthetic policy edit; checks are a separate explicit command."""
from dataclasses import asdict
import json
from edits import EditTools, ToolCall, Final, run, review_package

FILES={
    'tracker/policy.py':'def can_close_issue(role):\n    return role == "maintainer"\n',
    'tracker/views.py':'from tracker.policy import can_close_issue\n\ndef close_button_enabled(role):\n    return can_close_issue(role)\n',
}
TASK='Permit both maintainers and administrators to close issues; deny other roles.'

class ScriptedEdit:
    def next(self, task, events):
        results=[e.data['result'] for e in events if e.kind=='tool_result']
        if not results:
            return ToolCall('read','read_file',{'path':'tracker/policy.py'})
        if not results[-1]['ok']:
            return Final('The edit could not be prepared; inspect the recorded failure.')
        if len(results)==1:
            return ToolCall('edit','apply_edit',{
                'path':'tracker/policy.py', 'expected_sha256':results[-1]['data']['sha256'],
                'old':'role == "maintainer"','new':'role in {"maintainer", "administrator"}',
            })
        return Final('Candidate edit prepared. Behavioral checks have not run.')


def prepare():
    tools=EditTools(FILES,set(FILES),{'tracker/policy.py'})
    result=run(ScriptedEdit(),tools,TASK,max_steps=6)
    candidate=tools.snapshot()
    package=review_package(FILES,candidate,[asdict(e) for e in result.events])
    package['run_status']=result.status
    return candidate,package

if __name__=='__main__':print(json.dumps(prepare()[1],indent=2))
