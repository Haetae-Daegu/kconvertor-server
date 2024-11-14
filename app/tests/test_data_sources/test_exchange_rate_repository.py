from unittest.mock import create_autospec

import pytest
import requests

from app.api.data_sources.exchange_rate_repository import ExchangeRateRepository
from app.api.types import CountryCode


@pytest.fixture
def fake_request_handler():
    return create_autospec(requests)

class TestExchangeRateRepository:

    def test_should_raise_when_access_to_the_repository_is_forbidden(self, fake_request_handler):
        fake_request_handler.get.return_value.status_code = 403

        exchange_rate_repository = ExchangeRateRepository("", "", request_handler=fake_request_handler)

        with pytest.raises(ExchangeRateRepository.ForbiddenAccessError):
            exchange_rate_repository.get_exchange_rate_for_country(CountryCode("USD"))

    def test_should_raise_when_unexpected_error_occurs(self, fake_request_handler):
        fake_request_handler.get.return_value.status_code = 500

        exchange_rate_repository = ExchangeRateRepository("", "", request_handler=fake_request_handler)

        with pytest.raises(ExchangeRateRepository.UnexpectedResponseError):
            exchange_rate_repository.get_exchange_rate_for_country(CountryCode("USD"))

    def test_should_raise_when_request_handler_error_occurs(self, fake_request_handler):
        fake_request_handler.get.side_effect = requests.exceptions.RequestException

        exchange_rate_repository = ExchangeRateRepository("", "", request_handler=fake_request_handler)

        with pytest.raises(ExchangeRateRepository.RequestHandlerError):
            exchange_rate_repository.get_exchange_rate_for_country(CountryCode("USD"))

    def test_should_return_exchange_rate_for_given_country_code_when_it_exists(self, fake_request_handler):

        expected_rate = 2.0
        currency_to_convert = CountryCode("AUD")
        base_currency = CountryCode("USD")

        fake_request_handler.get.return_value.json.return_value = {
            "result": "success",
            "conversion_rates": {
                base_currency: 1,
                currency_to_convert: expected_rate
            }
        }
        fake_request_handler.get.return_value.status_code = 200


        exchange_rate_repository = ExchangeRateRepository("", "", request_handler=fake_request_handler)
        conversion_rates = exchange_rate_repository.get_exchange_rate_for_country(currency_to_convert, base_currency)

        assert conversion_rates == {
            base_currency: 1,
            currency_to_convert: expected_rate
        }

    def test_should_raise_when_base_country_code_does_not_exist_in_conversion_rates(self, fake_request_handler):
        base_currency = CountryCode("USD")

        fake_request_handler.get.return_value.status_code = 404

        exchange_rate_repository = ExchangeRateRepository("", "", request_handler=fake_request_handler)

        with pytest.raises(ExchangeRateRepository.CurrencyNotFoundError):
            exchange_rate_repository.get_exchange_rate_for_country(..., base_currency)


    def test_should_raise_when_target_currency_does_not_have_conversion_rate_for_given_base_currency(self, fake_request_handler):
        base_currency = CountryCode("USD")
        target_currency_to_convert = CountryCode("AUD")

        fake_request_handler.get.return_value.json.return_value = {
            "result": "success",
            "conversion_rates": {
                base_currency: 1,
            }
        }
        fake_request_handler.get.return_value.status_code = 200

        exchange_rate_repository = ExchangeRateRepository("", "", request_handler=fake_request_handler)

        with pytest.raises(ExchangeRateRepository.TargetCurrencyNotFoundError):
            exchange_rate_repository.get_exchange_rate_for_country(target_currency_to_convert, base_currency)


    @pytest.mark.parametrize("invalid_rate", [
        pytest.param("invalid_rate", id="when rate is a string"),
        pytest.param(-1.0, id="when rate is negative"),
    ])
    def test_should_raise_when_conversion_rate_is_not_a_valid_rate(self, fake_request_handler, invalid_rate):
        base_currency = CountryCode("USD")
        target_currency_to_convert = CountryCode("AUD")

        fake_request_handler.get.return_value.json.return_value = {
            "result": "success",
            "conversion_rates": {
                base_currency: 1,
                target_currency_to_convert: invalid_rate
            }
        }
        fake_request_handler.get.return_value.status_code = 200

        exchange_rate_repository = ExchangeRateRepository("", "", request_handler=fake_request_handler)

        with pytest.raises(ExchangeRateRepository.UnexpectedResponseError):
            exchange_rate_repository.get_exchange_rate_for_country(target_currency_to_convert, base_currency)
