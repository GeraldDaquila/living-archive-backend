from provider_bank import _workers_url


def test_workers_ai_model_path_preserves_route_segments():
    url = _workers_url("account-id", "@cf/zai-org/glm-4.7-flash")
    assert url == "https://api.cloudflare.com/client/v4/accounts/account-id/ai/run/@cf/zai-org/glm-4.7-flash"


def test_workers_ai_account_id_is_encoded_as_one_path_segment():
    url = _workers_url("account/id", "@cf/google/gemma-4-26b-a4b-it")
    assert "/accounts/account%2Fid/ai/run/@cf/google/gemma-4-26b-a4b-it" in url
