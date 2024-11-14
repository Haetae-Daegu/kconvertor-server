from unittest.mock import create_autospec

import pytest

from app.api.api import (
    CountryCode,
    ExchangeRate,
    ExchangeRateRepository,
    get_exchange_rate,
)


@pytest.fixture
def fake_exchange_rate_repository():
    fake_repo = create_autospec(ExchangeRateRepository, instance=True)

    yield fake_repo


class TestExchangeRate:

    def test_should_return_exchange_rate_for_country_provided(
        self, fake_exchange_rate_repository: ExchangeRateRepository
    ):
        expected_rate = 1485.9695

        expected_conversion = ExchangeRate(
            from_currency=CountryCode("EUR"),
            to_currency=CountryCode("KRW"),
            conversion_rate=expected_rate,
        )

        fake_exchange_rate_repository.get_exchange_rate_for_country.return_value = {
            CountryCode("EUR"): 1.0,
            CountryCode("KRW"): expected_rate,
        }

        exchange_rate = get_exchange_rate(
            fake_exchange_rate_repository, CountryCode("KRW")
        )

        assert exchange_rate == expected_conversion
