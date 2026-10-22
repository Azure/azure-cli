# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Compatibility for silo resource envelopes, origin reads and async responses."""

from functools import partial
from urllib.parse import unquote, urlsplit

from azure.core.exceptions import ResourceExistsError
from azure.cli.core.aaz import AAZStrType
from azure.cli.core.azclierror import AzureResponseError, InvalidArgumentValueError
from knack.log import get_logger

from ..aaz.latest.appservice.plan.silo import (
    Create as _PlanCreate, Update as _PlanUpdate, Delete as _PlanDelete,
    Show as _PlanShow, List as _PlanList, Wait as _PlanWait,
)
from ..aaz.latest.appservice.plan.silo.vnet_integration import List as _PlanVnetList
from ..aaz.latest.webapp.silo import (
    Create as _SiteCreate, Update as _SiteUpdate, Delete as _SiteDelete,
    Show as _SiteShow, List as _SiteList, Wait as _SiteWait,
)


logger = get_logger(__name__)


def _prefer_location_polling(response, hook=None):
    if hook:
        hook(response)
    headers = response.http_response.headers
    # Silo async-status reads return empty 202s; suppress that header so the SDK uses
    # the provided Location monitor. Remove once Azure-AsyncOperation returns status JSON.
    if headers.get("Location"):
        headers.pop("Azure-AsyncOperation", None)


def _read_origin_from_collection(operation, schema_builder):
    ctx = operation.ctx
    if ctx.args.silo.to_serialized_data().casefold() != "origin":
        return False
    # Origin point GET can return 404 while the collection contains it. Remove this
    # fallback once point GET is fixed; keep generated paging and response schemas.
    resources = SiteSiloList(cli_ctx=ctx.cli_ctx)(command_args={
        "subscription": ctx.subscription_id,
        "resource_group": ctx.args.resource_group.to_serialized_data(),
        "name": ctx.args.name.to_serialized_data(),
    })
    resource_id = unquote(urlsplit(operation.url).path).casefold()
    matches = [
        resource for resource in resources
        if isinstance(resource, dict) and isinstance(resource.get("id"), str) and
        unquote(resource["id"]).casefold() == resource_id
    ]
    if not matches:
        return False
    if len(matches) != 1:
        raise AzureResponseError("ARM returned duplicate origin resources in the silo collection.")
    resource = matches[0]
    resource_type = resource.get("type")
    if (not isinstance(resource_type, str) or resource_type.casefold() != "microsoft.web/sites/silos" or
            not isinstance(resource.get("properties"), dict)):
        raise AzureResponseError("ARM returned an invalid origin resource in the silo collection.")
    ctx.set_var("instance", resource, schema_builder=schema_builder)
    logger.warning(
        "Origin point GET returned HTTP 404; using the matching origin from the silo collection. "
        "Stamp-derived IP fields may be absent.")
    return True


def _include_location(schema):
    if not hasattr(schema, "location"):
        schema.location = AAZStrType()
    return schema


def _same_location(left, right):
    return left.replace(" ", "").casefold() == right.replace(" ", "").casefold()


def _silo_location(content):
    locations = [
        content.get("location"),
        content.get("properties", {}).get("siloLocation"),
    ]
    locations = [value for value in locations if value is not None]
    if not locations or any(not isinstance(value, str) or not value.strip() for value in locations):
        raise AzureResponseError("The silo resource does not include a usable location.")
    if any(not _same_location(locations[0], value) for value in locations[1:]):
        raise AzureResponseError("The silo resource contains conflicting location fields.")
    return locations[0]


def _create_content(content):
    content["location"] = _silo_location(content)
    return content


def _prepare_update(ctx, instance):
    location = _silo_location(instance.to_serialized_data())
    ctx.set_var("original_silo_location", location, schema_builder=AAZStrType)
    instance.location = location


def _complete_update(ctx, instance):
    original = ctx.vars.original_silo_location.to_serialized_data()
    content = instance.to_serialized_data()
    location = content.get("location")
    nested = content.get("properties", {}).get("siloLocation")
    if (not isinstance(location, str) or not _same_location(location, original) or
            (nested is not None and (not isinstance(nested, str) or not _same_location(nested, original)))):
        raise InvalidArgumentValueError("The location of an existing silo cannot be changed or removed.")
    instance.location = original


class PlanSiloCreate(_PlanCreate):
    class ServerFarmSiloResourcesCreateOrUpdateServerFarmSilo(
            _PlanCreate.ServerFarmSiloResourcesCreateOrUpdateServerFarmSilo):
        _schema_on_200_201 = None

        def __call__(self, *args, **kwargs):
            kwargs["raw_response_hook"] = partial(_prefer_location_polling, hook=kwargs.get("raw_response_hook"))
            return super().__call__(*args, **kwargs)

        @property
        def content(self):
            return _create_content(super().content)

        @classmethod
        def _build_schema_on_200_201(cls):
            return _include_location(super()._build_schema_on_200_201())


class PlanSiloUpdate(_PlanUpdate):
    def pre_instance_update(self, instance):
        _prepare_update(self.ctx, instance)

    def post_instance_update(self, instance):
        _complete_update(self.ctx, instance)

    class ServerFarmSiloResourcesGetServerFarmSilo(_PlanUpdate.ServerFarmSiloResourcesGetServerFarmSilo):
        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            return _include_location(super()._build_schema_on_200())

    class ServerFarmSiloResourcesCreateOrUpdateServerFarmSilo(
            _PlanUpdate.ServerFarmSiloResourcesCreateOrUpdateServerFarmSilo):
        _schema_on_200_201 = None

        def __call__(self, *args, **kwargs):
            kwargs["raw_response_hook"] = partial(_prefer_location_polling, hook=kwargs.get("raw_response_hook"))
            return super().__call__(*args, **kwargs)

        @classmethod
        def _build_schema_on_200_201(cls):
            return _include_location(super()._build_schema_on_200_201())


class PlanSiloDelete(_PlanDelete):
    class ServerFarmSiloResourcesDeleteServerFarmSilo(_PlanDelete.ServerFarmSiloResourcesDeleteServerFarmSilo):
        def __call__(self, *args, **kwargs):
            kwargs["raw_response_hook"] = partial(_prefer_location_polling, hook=kwargs.get("raw_response_hook"))
            return super().__call__(*args, **kwargs)

        def on_error(self, response):
            if response.status_code == 409:
                # Core's 409 mapping skips AAZ's case-insensitive formatter for App Service Code/Message fields.
                raise ResourceExistsError(response=response, error_format=self.ctx.get_error_format(self.error_format))
            return super().on_error(response)


class PlanSiloShow(_PlanShow):
    class ServerFarmSiloResourcesGetServerFarmSilo(_PlanShow.ServerFarmSiloResourcesGetServerFarmSilo):
        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            return _include_location(super()._build_schema_on_200())


class PlanSiloList(_PlanList):
    class ServerFarmSiloResourcesListServerFarmSilos(_PlanList.ServerFarmSiloResourcesListServerFarmSilos):
        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()
            _include_location(schema.value.Element)
            return schema


class PlanSiloWait(_PlanWait):
    class ServerFarmSiloResourcesGetServerFarmSilo(_PlanWait.ServerFarmSiloResourcesGetServerFarmSilo):
        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            return _include_location(super()._build_schema_on_200())


class PlanSiloVnetList(_PlanVnetList):
    class ServerFarmSiloResourcesGetServerFarmSiloVnetIntegrations(
            _PlanVnetList.ServerFarmSiloResourcesGetServerFarmSiloVnetIntegrations):
        def deserialize_http_content(self, session):
            data = super().deserialize_http_content(session)
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                return data
            # The draft spec declares an array, but the service wraps subnet properties
            # in an ARM envelope. Remove this adapter after the contract is regenerated.
            resource_type = data.get("type") if isinstance(data, dict) else None
            properties = data.get("properties") if isinstance(data, dict) else None
            if (not isinstance(resource_type, str) or
                    resource_type.casefold() != "microsoft.web/serverfarms/virtualnetworkintegrations" or
                    not isinstance(properties, list) or any(
                        not isinstance(item, dict) or not isinstance(item.get("subnetResourceId"), str) or
                        not item["subnetResourceId"].strip() for item in properties)):
                raise AzureResponseError("The plan-silo VNet integration API returned an unexpected response shape.")
            logger.warning(
                "Plan-silo VNet integrations returned an ARM properties array; using its subnet entries "
                "until the service specification is corrected.")
            return [{"properties": item} for item in properties]


class SiteSiloCreate(_SiteCreate):
    class SiteSiloResourcesCreateOrUpdateSiteSilo(_SiteCreate.SiteSiloResourcesCreateOrUpdateSiteSilo):
        _schema_on_200_201 = None

        def __call__(self, *args, **kwargs):
            kwargs["raw_response_hook"] = partial(_prefer_location_polling, hook=kwargs.get("raw_response_hook"))
            return super().__call__(*args, **kwargs)

        @property
        def content(self):
            return _create_content(super().content)

        @classmethod
        def _build_schema_on_200_201(cls):
            return _include_location(super()._build_schema_on_200_201())


class SiteSiloUpdate(_SiteUpdate):
    def pre_instance_update(self, instance):
        _prepare_update(self.ctx, instance)

    def post_instance_update(self, instance):
        _complete_update(self.ctx, instance)

    class SiteSiloResourcesGetSiteSilo(_SiteUpdate.SiteSiloResourcesGetSiteSilo):
        _schema_on_200 = None

        def on_error(self, response):
            if response.status_code == 404 and _read_origin_from_collection(self, self._build_schema_on_200):
                return None
            return super().on_error(response)

        @classmethod
        def _build_schema_on_200(cls):
            return _include_location(super()._build_schema_on_200())

    class SiteSiloResourcesCreateOrUpdateSiteSilo(_SiteUpdate.SiteSiloResourcesCreateOrUpdateSiteSilo):
        _schema_on_200_201 = None

        def __call__(self, *args, **kwargs):
            kwargs["raw_response_hook"] = partial(_prefer_location_polling, hook=kwargs.get("raw_response_hook"))
            return super().__call__(*args, **kwargs)

        @classmethod
        def _build_schema_on_200_201(cls):
            return _include_location(super()._build_schema_on_200_201())


class SiteSiloDelete(_SiteDelete):
    class SiteSiloResourcesDeleteSiteSilo(_SiteDelete.SiteSiloResourcesDeleteSiteSilo):
        def __call__(self, *args, **kwargs):
            kwargs["raw_response_hook"] = partial(_prefer_location_polling, hook=kwargs.get("raw_response_hook"))
            return super().__call__(*args, **kwargs)


class SiteSiloShow(_SiteShow):
    class SiteSiloResourcesGetSiteSilo(_SiteShow.SiteSiloResourcesGetSiteSilo):
        _schema_on_200 = None

        def on_error(self, response):
            if response.status_code == 404 and _read_origin_from_collection(self, self._build_schema_on_200):
                return None
            return super().on_error(response)

        @classmethod
        def _build_schema_on_200(cls):
            return _include_location(super()._build_schema_on_200())


class SiteSiloList(_SiteList):
    class SiteSiloResourcesListSiteSilos(_SiteList.SiteSiloResourcesListSiteSilos):
        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()
            _include_location(schema.value.Element)
            return schema


class SiteSiloWait(_SiteWait):
    class SiteSiloResourcesGetSiteSilo(_SiteWait.SiteSiloResourcesGetSiteSilo):
        _schema_on_200 = None

        def on_error(self, response):
            if response.status_code == 404 and _read_origin_from_collection(self, self._build_schema_on_200):
                return None
            return super().on_error(response)

        @classmethod
        def _build_schema_on_200(cls):
            return _include_location(super()._build_schema_on_200())
