import pytest
from src.utils.pdf_generator import generate_claim_slip_pdf
from src.ui.translations import TRANSLATIONS
from src.agent.orchestrator import AgentOrchestrator
from src.llm.client import SmartDeterministicClient

def test_generate_pdf_bytes():
    pdf = generate_claim_slip_pdf(
        customer_name='Priya Nair',
        pnr='SK4821X',
        contact_email='priya@email.com',
        contact_phone='+91 9999999999',
        flight_number='SK-204',
        route='DEL → GOI',
        flight_status='CANCELLED',
        delay_info='Operational Cancellation',
        actions_taken=['refund', 'rebook'],
    )
    assert isinstance(pdf, bytes)
    assert len(pdf) > 1000
    assert pdf.startswith(b'%PDF')

def test_translations_keys_exist():
    assert 'en' in TRANSLATIONS
    assert 'hi' in TRANSLATIONS
    assert 'portal_title' in TRANSLATIONS['hi']
    assert 'download_claim_pdf' in TRANSLATIONS['hi']

def test_hindi_response_generation():
    client = SmartDeterministicClient()
    orch = AgentOrchestrator(llm_client=client)
    orch.set_customer('Priya Nair')
    resp = orch.handle_message('मुझे रिफंड चाहिए', language='hi')
    assert resp.message != ''
    assert any(w in resp.message for w in ['रिफंड', 'रुपये', 'खाते', 'प्रक्रिया', 'उड़ान'])
