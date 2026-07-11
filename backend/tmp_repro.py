from app.graph.interview.graph import interview_graph
from app.graph.optimizer.state import InterviewState

initial_state = {
    'workflow_type': 'interview',
    'user_goal': 'Generic Interview',
    'target_role': 'Backend',
    'user_id': 'u',
    'job_id': 'iv-test',
    'jd_text': None,
    'resume_data': None,
    'resume_review': None,
    'ats_result': None,
    'jd_data': None,
    'interview': InterviewState(),
    'completed_agents': [],
    'errors': [],
    'status': 'pending',
}

print('initial_interview', initial_state['interview'].model_dump())
result = interview_graph.invoke(initial_state)
print('result_keys', result.keys())
print('result_interview_type', type(result['interview']))
print('result_interview', result['interview'])
print('result_interview_dict', result['interview'].model_dump() if hasattr(result['interview'], 'model_dump') else result['interview'])
print('completed_agents', result.get('completed_agents'))
print('next_agent', result.get('next_agent'))
