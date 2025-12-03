from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import cdk8s as _cdk8s_d3d9af27
import constructs as _constructs_77d1e7e8


class Application(
    _cdk8s_d3d9af27.ApiObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="ioargoproj.Application",
):
    '''Application is a definition of Application resource.

    :schema: Application
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        metadata: typing.Union[_cdk8s_d3d9af27.ApiObjectMetadata, typing.Dict[builtins.str, typing.Any]],
        spec: typing.Union["ApplicationSpec", typing.Dict[builtins.str, typing.Any]],
        operation: typing.Optional[typing.Union["ApplicationOperation", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Defines a "Application" API object.

        :param scope: the scope in which to define this object.
        :param id: a scope-local name for the object.
        :param metadata: 
        :param spec: ApplicationSpec represents desired application state. Contains link to repository with application definition and additional parameters link definition revision.
        :param operation: Operation contains information about a requested or running operation.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9fadc55084560f240c2c9e6a99b09bb072446fb64fdbc835fefe1e6223a2cc52)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ApplicationProps(metadata=metadata, spec=spec, operation=operation)

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="manifest")
    @builtins.classmethod
    def manifest(
        cls,
        *,
        metadata: typing.Union[_cdk8s_d3d9af27.ApiObjectMetadata, typing.Dict[builtins.str, typing.Any]],
        spec: typing.Union["ApplicationSpec", typing.Dict[builtins.str, typing.Any]],
        operation: typing.Optional[typing.Union["ApplicationOperation", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> typing.Any:
        '''Renders a Kubernetes manifest for "Application".

        This can be used to inline resource manifests inside other objects (e.g. as templates).

        :param metadata: 
        :param spec: ApplicationSpec represents desired application state. Contains link to repository with application definition and additional parameters link definition revision.
        :param operation: Operation contains information about a requested or running operation.
        '''
        props = ApplicationProps(metadata=metadata, spec=spec, operation=operation)

        return typing.cast(typing.Any, jsii.sinvoke(cls, "manifest", [props]))

    @jsii.member(jsii_name="toJson")
    def to_json(self) -> typing.Any:
        '''Renders the object to Kubernetes JSON.'''
        return typing.cast(typing.Any, jsii.invoke(self, "toJson", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="GVK")
    def GVK(cls) -> _cdk8s_d3d9af27.GroupVersionKind:
        '''Returns the apiVersion and kind for "Application".'''
        return typing.cast(_cdk8s_d3d9af27.GroupVersionKind, jsii.sget(cls, "GVK"))


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperation",
    jsii_struct_bases=[],
    name_mapping={
        "info": "info",
        "initiated_by": "initiatedBy",
        "retry": "retry",
        "sync": "sync",
    },
)
class ApplicationOperation:
    def __init__(
        self,
        *,
        info: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationInfo", typing.Dict[builtins.str, typing.Any]]]] = None,
        initiated_by: typing.Optional[typing.Union["ApplicationOperationInitiatedBy", typing.Dict[builtins.str, typing.Any]]] = None,
        retry: typing.Optional[typing.Union["ApplicationOperationRetry", typing.Dict[builtins.str, typing.Any]]] = None,
        sync: typing.Optional[typing.Union["ApplicationOperationSync", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Operation contains information about a requested or running operation.

        :param info: Info is a list of informational items for this operation.
        :param initiated_by: InitiatedBy contains information about who initiated the operations.
        :param retry: Retry controls the strategy to apply if a sync fails.
        :param sync: Sync contains parameters for the operation.

        :schema: ApplicationOperation
        '''
        if isinstance(initiated_by, dict):
            initiated_by = ApplicationOperationInitiatedBy(**initiated_by)
        if isinstance(retry, dict):
            retry = ApplicationOperationRetry(**retry)
        if isinstance(sync, dict):
            sync = ApplicationOperationSync(**sync)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fc7489c6e9afd59a19ebe90297e21cd3b82fa6c82434517bb3ec2d7714eaa981)
            check_type(argname="argument info", value=info, expected_type=type_hints["info"])
            check_type(argname="argument initiated_by", value=initiated_by, expected_type=type_hints["initiated_by"])
            check_type(argname="argument retry", value=retry, expected_type=type_hints["retry"])
            check_type(argname="argument sync", value=sync, expected_type=type_hints["sync"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if info is not None:
            self._values["info"] = info
        if initiated_by is not None:
            self._values["initiated_by"] = initiated_by
        if retry is not None:
            self._values["retry"] = retry
        if sync is not None:
            self._values["sync"] = sync

    @builtins.property
    def info(self) -> typing.Optional[typing.List["ApplicationOperationInfo"]]:
        '''Info is a list of informational items for this operation.

        :schema: ApplicationOperation#info
        '''
        result = self._values.get("info")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationInfo"]], result)

    @builtins.property
    def initiated_by(self) -> typing.Optional["ApplicationOperationInitiatedBy"]:
        '''InitiatedBy contains information about who initiated the operations.

        :schema: ApplicationOperation#initiatedBy
        '''
        result = self._values.get("initiated_by")
        return typing.cast(typing.Optional["ApplicationOperationInitiatedBy"], result)

    @builtins.property
    def retry(self) -> typing.Optional["ApplicationOperationRetry"]:
        '''Retry controls the strategy to apply if a sync fails.

        :schema: ApplicationOperation#retry
        '''
        result = self._values.get("retry")
        return typing.cast(typing.Optional["ApplicationOperationRetry"], result)

    @builtins.property
    def sync(self) -> typing.Optional["ApplicationOperationSync"]:
        '''Sync contains parameters for the operation.

        :schema: ApplicationOperation#sync
        '''
        result = self._values.get("sync")
        return typing.cast(typing.Optional["ApplicationOperationSync"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperation(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationInfo",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value"},
)
class ApplicationOperationInfo:
    def __init__(self, *, name: builtins.str, value: builtins.str) -> None:
        '''
        :param name: 
        :param value: 

        :schema: ApplicationOperationInfo
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d9d029733dc89d70b49466bd73599fc2cbabade797ce042fdc2d5e7fc8bbb145)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationOperationInfo#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationOperationInfo#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationInfo(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationInitiatedBy",
    jsii_struct_bases=[],
    name_mapping={"automated": "automated", "username": "username"},
)
class ApplicationOperationInitiatedBy:
    def __init__(
        self,
        *,
        automated: typing.Optional[builtins.bool] = None,
        username: typing.Optional[builtins.str] = None,
    ) -> None:
        '''InitiatedBy contains information about who initiated the operations.

        :param automated: Automated is set to true if operation was initiated automatically by the application controller.
        :param username: Username contains the name of a user who started operation.

        :schema: ApplicationOperationInitiatedBy
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ebb4ba1ffa2baf2a89537dc6954e1da91dc957dd881e0b03f84263feaca63e80)
            check_type(argname="argument automated", value=automated, expected_type=type_hints["automated"])
            check_type(argname="argument username", value=username, expected_type=type_hints["username"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if automated is not None:
            self._values["automated"] = automated
        if username is not None:
            self._values["username"] = username

    @builtins.property
    def automated(self) -> typing.Optional[builtins.bool]:
        '''Automated is set to true if operation was initiated automatically by the application controller.

        :schema: ApplicationOperationInitiatedBy#automated
        '''
        result = self._values.get("automated")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def username(self) -> typing.Optional[builtins.str]:
        '''Username contains the name of a user who started operation.

        :schema: ApplicationOperationInitiatedBy#username
        '''
        result = self._values.get("username")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationInitiatedBy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationRetry",
    jsii_struct_bases=[],
    name_mapping={"backoff": "backoff", "limit": "limit", "refresh": "refresh"},
)
class ApplicationOperationRetry:
    def __init__(
        self,
        *,
        backoff: typing.Optional[typing.Union["ApplicationOperationRetryBackoff", typing.Dict[builtins.str, typing.Any]]] = None,
        limit: typing.Optional[jsii.Number] = None,
        refresh: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Retry controls the strategy to apply if a sync fails.

        :param backoff: Backoff controls how to backoff on subsequent retries of failed syncs.
        :param limit: Limit is the maximum number of attempts for retrying a failed sync. If set to 0, no retries will be performed.
        :param refresh: Refresh indicates if the latest revision should be used on retry instead of the initial one (default: false).

        :schema: ApplicationOperationRetry
        '''
        if isinstance(backoff, dict):
            backoff = ApplicationOperationRetryBackoff(**backoff)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4ac6fe22df0bbd4d619fea202e4f3000095deed912da8875517926ae5f30ece5)
            check_type(argname="argument backoff", value=backoff, expected_type=type_hints["backoff"])
            check_type(argname="argument limit", value=limit, expected_type=type_hints["limit"])
            check_type(argname="argument refresh", value=refresh, expected_type=type_hints["refresh"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if backoff is not None:
            self._values["backoff"] = backoff
        if limit is not None:
            self._values["limit"] = limit
        if refresh is not None:
            self._values["refresh"] = refresh

    @builtins.property
    def backoff(self) -> typing.Optional["ApplicationOperationRetryBackoff"]:
        '''Backoff controls how to backoff on subsequent retries of failed syncs.

        :schema: ApplicationOperationRetry#backoff
        '''
        result = self._values.get("backoff")
        return typing.cast(typing.Optional["ApplicationOperationRetryBackoff"], result)

    @builtins.property
    def limit(self) -> typing.Optional[jsii.Number]:
        '''Limit is the maximum number of attempts for retrying a failed sync.

        If set to 0, no retries will be performed.

        :schema: ApplicationOperationRetry#limit
        '''
        result = self._values.get("limit")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def refresh(self) -> typing.Optional[builtins.bool]:
        '''Refresh indicates if the latest revision should be used on retry instead of the initial one (default: false).

        :schema: ApplicationOperationRetry#refresh
        '''
        result = self._values.get("refresh")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationRetry(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationRetryBackoff",
    jsii_struct_bases=[],
    name_mapping={
        "duration": "duration",
        "factor": "factor",
        "max_duration": "maxDuration",
    },
)
class ApplicationOperationRetryBackoff:
    def __init__(
        self,
        *,
        duration: typing.Optional[builtins.str] = None,
        factor: typing.Optional[jsii.Number] = None,
        max_duration: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Backoff controls how to backoff on subsequent retries of failed syncs.

        :param duration: Duration is the amount to back off. Default unit is seconds, but could also be a duration (e.g. "2m", "1h")
        :param factor: Factor is a factor to multiply the base duration after each failed retry.
        :param max_duration: MaxDuration is the maximum amount of time allowed for the backoff strategy.

        :schema: ApplicationOperationRetryBackoff
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e0275a64a928a93eea988e920bdff4cf240f265cb687299af5c4a92644eb5d7b)
            check_type(argname="argument duration", value=duration, expected_type=type_hints["duration"])
            check_type(argname="argument factor", value=factor, expected_type=type_hints["factor"])
            check_type(argname="argument max_duration", value=max_duration, expected_type=type_hints["max_duration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if duration is not None:
            self._values["duration"] = duration
        if factor is not None:
            self._values["factor"] = factor
        if max_duration is not None:
            self._values["max_duration"] = max_duration

    @builtins.property
    def duration(self) -> typing.Optional[builtins.str]:
        '''Duration is the amount to back off.

        Default unit is seconds, but could also be a duration (e.g. "2m", "1h")

        :schema: ApplicationOperationRetryBackoff#duration
        '''
        result = self._values.get("duration")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def factor(self) -> typing.Optional[jsii.Number]:
        '''Factor is a factor to multiply the base duration after each failed retry.

        :schema: ApplicationOperationRetryBackoff#factor
        '''
        result = self._values.get("factor")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_duration(self) -> typing.Optional[builtins.str]:
        '''MaxDuration is the maximum amount of time allowed for the backoff strategy.

        :schema: ApplicationOperationRetryBackoff#maxDuration
        '''
        result = self._values.get("max_duration")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationRetryBackoff(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSync",
    jsii_struct_bases=[],
    name_mapping={
        "auto_heal_attempts_count": "autoHealAttemptsCount",
        "dry_run": "dryRun",
        "manifests": "manifests",
        "prune": "prune",
        "resources": "resources",
        "revision": "revision",
        "revisions": "revisions",
        "source": "source",
        "sources": "sources",
        "sync_options": "syncOptions",
        "sync_strategy": "syncStrategy",
    },
)
class ApplicationOperationSync:
    def __init__(
        self,
        *,
        auto_heal_attempts_count: typing.Optional[jsii.Number] = None,
        dry_run: typing.Optional[builtins.bool] = None,
        manifests: typing.Optional[typing.Sequence[builtins.str]] = None,
        prune: typing.Optional[builtins.bool] = None,
        resources: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncResources", typing.Dict[builtins.str, typing.Any]]]] = None,
        revision: typing.Optional[builtins.str] = None,
        revisions: typing.Optional[typing.Sequence[builtins.str]] = None,
        source: typing.Optional[typing.Union["ApplicationOperationSyncSource", typing.Dict[builtins.str, typing.Any]]] = None,
        sources: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSources", typing.Dict[builtins.str, typing.Any]]]] = None,
        sync_options: typing.Optional[typing.Sequence[builtins.str]] = None,
        sync_strategy: typing.Optional[typing.Union["ApplicationOperationSyncSyncStrategy", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Sync contains parameters for the operation.

        :param auto_heal_attempts_count: SelfHealAttemptsCount contains the number of auto-heal attempts.
        :param dry_run: DryRun specifies to perform a ``kubectl apply --dry-run`` without actually performing the sync.
        :param manifests: Manifests is an optional field that overrides sync source with a local directory for development.
        :param prune: Prune specifies to delete resources from the cluster that are no longer tracked in git.
        :param resources: Resources describes which resources shall be part of the sync.
        :param revision: Revision is the revision (Git) or chart version (Helm) which to sync the application to If omitted, will use the revision specified in app spec.
        :param revisions: Revisions is the list of revision (Git) or chart version (Helm) which to sync each source in sources field for the application to If omitted, will use the revision specified in app spec.
        :param source: Source overrides the source definition set in the application. This is typically set in a Rollback operation and is nil during a Sync operation
        :param sources: Sources overrides the source definition set in the application. This is typically set in a Rollback operation and is nil during a Sync operation
        :param sync_options: SyncOptions provide per-sync sync-options, e.g. Validate=false.
        :param sync_strategy: SyncStrategy describes how to perform the sync.

        :schema: ApplicationOperationSync
        '''
        if isinstance(source, dict):
            source = ApplicationOperationSyncSource(**source)
        if isinstance(sync_strategy, dict):
            sync_strategy = ApplicationOperationSyncSyncStrategy(**sync_strategy)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a6298dfe0e54c7f7cb26e8308cab95d46ae758c3f7c7d8ec80166d4234e79be7)
            check_type(argname="argument auto_heal_attempts_count", value=auto_heal_attempts_count, expected_type=type_hints["auto_heal_attempts_count"])
            check_type(argname="argument dry_run", value=dry_run, expected_type=type_hints["dry_run"])
            check_type(argname="argument manifests", value=manifests, expected_type=type_hints["manifests"])
            check_type(argname="argument prune", value=prune, expected_type=type_hints["prune"])
            check_type(argname="argument resources", value=resources, expected_type=type_hints["resources"])
            check_type(argname="argument revision", value=revision, expected_type=type_hints["revision"])
            check_type(argname="argument revisions", value=revisions, expected_type=type_hints["revisions"])
            check_type(argname="argument source", value=source, expected_type=type_hints["source"])
            check_type(argname="argument sources", value=sources, expected_type=type_hints["sources"])
            check_type(argname="argument sync_options", value=sync_options, expected_type=type_hints["sync_options"])
            check_type(argname="argument sync_strategy", value=sync_strategy, expected_type=type_hints["sync_strategy"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if auto_heal_attempts_count is not None:
            self._values["auto_heal_attempts_count"] = auto_heal_attempts_count
        if dry_run is not None:
            self._values["dry_run"] = dry_run
        if manifests is not None:
            self._values["manifests"] = manifests
        if prune is not None:
            self._values["prune"] = prune
        if resources is not None:
            self._values["resources"] = resources
        if revision is not None:
            self._values["revision"] = revision
        if revisions is not None:
            self._values["revisions"] = revisions
        if source is not None:
            self._values["source"] = source
        if sources is not None:
            self._values["sources"] = sources
        if sync_options is not None:
            self._values["sync_options"] = sync_options
        if sync_strategy is not None:
            self._values["sync_strategy"] = sync_strategy

    @builtins.property
    def auto_heal_attempts_count(self) -> typing.Optional[jsii.Number]:
        '''SelfHealAttemptsCount contains the number of auto-heal attempts.

        :schema: ApplicationOperationSync#autoHealAttemptsCount
        '''
        result = self._values.get("auto_heal_attempts_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def dry_run(self) -> typing.Optional[builtins.bool]:
        '''DryRun specifies to perform a ``kubectl apply --dry-run`` without actually performing the sync.

        :schema: ApplicationOperationSync#dryRun
        '''
        result = self._values.get("dry_run")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def manifests(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Manifests is an optional field that overrides sync source with a local directory for development.

        :schema: ApplicationOperationSync#manifests
        '''
        result = self._values.get("manifests")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def prune(self) -> typing.Optional[builtins.bool]:
        '''Prune specifies to delete resources from the cluster that are no longer tracked in git.

        :schema: ApplicationOperationSync#prune
        '''
        result = self._values.get("prune")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def resources(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncResources"]]:
        '''Resources describes which resources shall be part of the sync.

        :schema: ApplicationOperationSync#resources
        '''
        result = self._values.get("resources")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncResources"]], result)

    @builtins.property
    def revision(self) -> typing.Optional[builtins.str]:
        '''Revision is the revision (Git) or chart version (Helm) which to sync the application to If omitted, will use the revision specified in app spec.

        :schema: ApplicationOperationSync#revision
        '''
        result = self._values.get("revision")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def revisions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Revisions is the list of revision (Git) or chart version (Helm) which to sync each source in sources field for the application to If omitted, will use the revision specified in app spec.

        :schema: ApplicationOperationSync#revisions
        '''
        result = self._values.get("revisions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def source(self) -> typing.Optional["ApplicationOperationSyncSource"]:
        '''Source overrides the source definition set in the application.

        This is typically set in a Rollback operation and is nil during a Sync operation

        :schema: ApplicationOperationSync#source
        '''
        result = self._values.get("source")
        return typing.cast(typing.Optional["ApplicationOperationSyncSource"], result)

    @builtins.property
    def sources(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSources"]]:
        '''Sources overrides the source definition set in the application.

        This is typically set in a Rollback operation and is nil during a Sync operation

        :schema: ApplicationOperationSync#sources
        '''
        result = self._values.get("sources")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSources"]], result)

    @builtins.property
    def sync_options(self) -> typing.Optional[typing.List[builtins.str]]:
        '''SyncOptions provide per-sync sync-options, e.g. Validate=false.

        :schema: ApplicationOperationSync#syncOptions
        '''
        result = self._values.get("sync_options")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def sync_strategy(self) -> typing.Optional["ApplicationOperationSyncSyncStrategy"]:
        '''SyncStrategy describes how to perform the sync.

        :schema: ApplicationOperationSync#syncStrategy
        '''
        result = self._values.get("sync_strategy")
        return typing.cast(typing.Optional["ApplicationOperationSyncSyncStrategy"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSync(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncResources",
    jsii_struct_bases=[],
    name_mapping={
        "kind": "kind",
        "name": "name",
        "group": "group",
        "namespace": "namespace",
    },
)
class ApplicationOperationSyncResources:
    def __init__(
        self,
        *,
        kind: builtins.str,
        name: builtins.str,
        group: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
    ) -> None:
        '''SyncOperationResource contains resources to sync.

        :param kind: 
        :param name: 
        :param group: 
        :param namespace: 

        :schema: ApplicationOperationSyncResources
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__57c79a8c21b61f24d9d60f6ab430d024ad1062593420b1cc70bbcab5ad0251ee)
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument group", value=group, expected_type=type_hints["group"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "kind": kind,
            "name": name,
        }
        if group is not None:
            self._values["group"] = group
        if namespace is not None:
            self._values["namespace"] = namespace

    @builtins.property
    def kind(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncResources#kind
        '''
        result = self._values.get("kind")
        assert result is not None, "Required property 'kind' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncResources#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def group(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncResources#group
        '''
        result = self._values.get("group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncResources#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncResources(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSource",
    jsii_struct_bases=[],
    name_mapping={
        "repo_url": "repoUrl",
        "chart": "chart",
        "directory": "directory",
        "helm": "helm",
        "kustomize": "kustomize",
        "name": "name",
        "path": "path",
        "plugin": "plugin",
        "ref": "ref",
        "target_revision": "targetRevision",
    },
)
class ApplicationOperationSyncSource:
    def __init__(
        self,
        *,
        repo_url: builtins.str,
        chart: typing.Optional[builtins.str] = None,
        directory: typing.Optional[typing.Union["ApplicationOperationSyncSourceDirectory", typing.Dict[builtins.str, typing.Any]]] = None,
        helm: typing.Optional[typing.Union["ApplicationOperationSyncSourceHelm", typing.Dict[builtins.str, typing.Any]]] = None,
        kustomize: typing.Optional[typing.Union["ApplicationOperationSyncSourceKustomize", typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        plugin: typing.Optional[typing.Union["ApplicationOperationSyncSourcePlugin", typing.Dict[builtins.str, typing.Any]]] = None,
        ref: typing.Optional[builtins.str] = None,
        target_revision: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Source overrides the source definition set in the application.

        This is typically set in a Rollback operation and is nil during a Sync operation

        :param repo_url: RepoURL is the URL to the repository (Git or Helm) that contains the application manifests.
        :param chart: Chart is a Helm chart name, and must be specified for applications sourced from a Helm repo.
        :param directory: Directory holds path/directory specific options.
        :param helm: Helm holds helm specific options.
        :param kustomize: Kustomize holds kustomize specific options.
        :param name: Name is used to refer to a source and is displayed in the UI. It is used in multi-source Applications.
        :param path: Path is a directory path within the Git repository, and is only valid for applications sourced from Git.
        :param plugin: Plugin holds config management plugin specific options.
        :param ref: Ref is reference to another source within sources field. This field will not be used if used with a ``source`` tag.
        :param target_revision: TargetRevision defines the revision of the source to sync the application to. In case of Git, this can be commit, tag, or branch. If omitted, will equal to HEAD. In case of Helm, this is a semver tag for the Chart's version.

        :schema: ApplicationOperationSyncSource
        '''
        if isinstance(directory, dict):
            directory = ApplicationOperationSyncSourceDirectory(**directory)
        if isinstance(helm, dict):
            helm = ApplicationOperationSyncSourceHelm(**helm)
        if isinstance(kustomize, dict):
            kustomize = ApplicationOperationSyncSourceKustomize(**kustomize)
        if isinstance(plugin, dict):
            plugin = ApplicationOperationSyncSourcePlugin(**plugin)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__380a721d40f74f3998504dda80bc9fbf987a3ececf1c01c3c1316da13bf2f238)
            check_type(argname="argument repo_url", value=repo_url, expected_type=type_hints["repo_url"])
            check_type(argname="argument chart", value=chart, expected_type=type_hints["chart"])
            check_type(argname="argument directory", value=directory, expected_type=type_hints["directory"])
            check_type(argname="argument helm", value=helm, expected_type=type_hints["helm"])
            check_type(argname="argument kustomize", value=kustomize, expected_type=type_hints["kustomize"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument plugin", value=plugin, expected_type=type_hints["plugin"])
            check_type(argname="argument ref", value=ref, expected_type=type_hints["ref"])
            check_type(argname="argument target_revision", value=target_revision, expected_type=type_hints["target_revision"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "repo_url": repo_url,
        }
        if chart is not None:
            self._values["chart"] = chart
        if directory is not None:
            self._values["directory"] = directory
        if helm is not None:
            self._values["helm"] = helm
        if kustomize is not None:
            self._values["kustomize"] = kustomize
        if name is not None:
            self._values["name"] = name
        if path is not None:
            self._values["path"] = path
        if plugin is not None:
            self._values["plugin"] = plugin
        if ref is not None:
            self._values["ref"] = ref
        if target_revision is not None:
            self._values["target_revision"] = target_revision

    @builtins.property
    def repo_url(self) -> builtins.str:
        '''RepoURL is the URL to the repository (Git or Helm) that contains the application manifests.

        :schema: ApplicationOperationSyncSource#repoURL
        '''
        result = self._values.get("repo_url")
        assert result is not None, "Required property 'repo_url' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def chart(self) -> typing.Optional[builtins.str]:
        '''Chart is a Helm chart name, and must be specified for applications sourced from a Helm repo.

        :schema: ApplicationOperationSyncSource#chart
        '''
        result = self._values.get("chart")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def directory(self) -> typing.Optional["ApplicationOperationSyncSourceDirectory"]:
        '''Directory holds path/directory specific options.

        :schema: ApplicationOperationSyncSource#directory
        '''
        result = self._values.get("directory")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourceDirectory"], result)

    @builtins.property
    def helm(self) -> typing.Optional["ApplicationOperationSyncSourceHelm"]:
        '''Helm holds helm specific options.

        :schema: ApplicationOperationSyncSource#helm
        '''
        result = self._values.get("helm")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourceHelm"], result)

    @builtins.property
    def kustomize(self) -> typing.Optional["ApplicationOperationSyncSourceKustomize"]:
        '''Kustomize holds kustomize specific options.

        :schema: ApplicationOperationSyncSource#kustomize
        '''
        result = self._values.get("kustomize")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourceKustomize"], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is used to refer to a source and is displayed in the UI.

        It is used in multi-source Applications.

        :schema: ApplicationOperationSyncSource#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Path is a directory path within the Git repository, and is only valid for applications sourced from Git.

        :schema: ApplicationOperationSyncSource#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def plugin(self) -> typing.Optional["ApplicationOperationSyncSourcePlugin"]:
        '''Plugin holds config management plugin specific options.

        :schema: ApplicationOperationSyncSource#plugin
        '''
        result = self._values.get("plugin")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourcePlugin"], result)

    @builtins.property
    def ref(self) -> typing.Optional[builtins.str]:
        '''Ref is reference to another source within sources field.

        This field will not be used if used with a ``source`` tag.

        :schema: ApplicationOperationSyncSource#ref
        '''
        result = self._values.get("ref")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_revision(self) -> typing.Optional[builtins.str]:
        '''TargetRevision defines the revision of the source to sync the application to.

        In case of Git, this can be commit, tag, or branch. If omitted, will equal to HEAD.
        In case of Helm, this is a semver tag for the Chart's version.

        :schema: ApplicationOperationSyncSource#targetRevision
        '''
        result = self._values.get("target_revision")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceDirectory",
    jsii_struct_bases=[],
    name_mapping={
        "exclude": "exclude",
        "include": "include",
        "jsonnet": "jsonnet",
        "recurse": "recurse",
    },
)
class ApplicationOperationSyncSourceDirectory:
    def __init__(
        self,
        *,
        exclude: typing.Optional[builtins.str] = None,
        include: typing.Optional[builtins.str] = None,
        jsonnet: typing.Optional[typing.Union["ApplicationOperationSyncSourceDirectoryJsonnet", typing.Dict[builtins.str, typing.Any]]] = None,
        recurse: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Directory holds path/directory specific options.

        :param exclude: Exclude contains a glob pattern to match paths against that should be explicitly excluded from being used during manifest generation.
        :param include: Include contains a glob pattern to match paths against that should be explicitly included during manifest generation.
        :param jsonnet: Jsonnet holds options specific to Jsonnet.
        :param recurse: Recurse specifies whether to scan a directory recursively for manifests.

        :schema: ApplicationOperationSyncSourceDirectory
        '''
        if isinstance(jsonnet, dict):
            jsonnet = ApplicationOperationSyncSourceDirectoryJsonnet(**jsonnet)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__68dd854000d14031a8145af1c8c3ddaf12c86dd9ecc65104616e077a2172579a)
            check_type(argname="argument exclude", value=exclude, expected_type=type_hints["exclude"])
            check_type(argname="argument include", value=include, expected_type=type_hints["include"])
            check_type(argname="argument jsonnet", value=jsonnet, expected_type=type_hints["jsonnet"])
            check_type(argname="argument recurse", value=recurse, expected_type=type_hints["recurse"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if exclude is not None:
            self._values["exclude"] = exclude
        if include is not None:
            self._values["include"] = include
        if jsonnet is not None:
            self._values["jsonnet"] = jsonnet
        if recurse is not None:
            self._values["recurse"] = recurse

    @builtins.property
    def exclude(self) -> typing.Optional[builtins.str]:
        '''Exclude contains a glob pattern to match paths against that should be explicitly excluded from being used during manifest generation.

        :schema: ApplicationOperationSyncSourceDirectory#exclude
        '''
        result = self._values.get("exclude")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def include(self) -> typing.Optional[builtins.str]:
        '''Include contains a glob pattern to match paths against that should be explicitly included during manifest generation.

        :schema: ApplicationOperationSyncSourceDirectory#include
        '''
        result = self._values.get("include")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jsonnet(
        self,
    ) -> typing.Optional["ApplicationOperationSyncSourceDirectoryJsonnet"]:
        '''Jsonnet holds options specific to Jsonnet.

        :schema: ApplicationOperationSyncSourceDirectory#jsonnet
        '''
        result = self._values.get("jsonnet")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourceDirectoryJsonnet"], result)

    @builtins.property
    def recurse(self) -> typing.Optional[builtins.bool]:
        '''Recurse specifies whether to scan a directory recursively for manifests.

        :schema: ApplicationOperationSyncSourceDirectory#recurse
        '''
        result = self._values.get("recurse")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceDirectory(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceDirectoryJsonnet",
    jsii_struct_bases=[],
    name_mapping={"ext_vars": "extVars", "libs": "libs", "tlas": "tlas"},
)
class ApplicationOperationSyncSourceDirectoryJsonnet:
    def __init__(
        self,
        *,
        ext_vars: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourceDirectoryJsonnetExtVars", typing.Dict[builtins.str, typing.Any]]]] = None,
        libs: typing.Optional[typing.Sequence[builtins.str]] = None,
        tlas: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourceDirectoryJsonnetTlas", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Jsonnet holds options specific to Jsonnet.

        :param ext_vars: ExtVars is a list of Jsonnet External Variables.
        :param libs: Additional library search dirs.
        :param tlas: TLAS is a list of Jsonnet Top-level Arguments.

        :schema: ApplicationOperationSyncSourceDirectoryJsonnet
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8252a821d880e55f2ed4fc9fa8d53507d0a79edefdfb3568350ba31c19e8e6b6)
            check_type(argname="argument ext_vars", value=ext_vars, expected_type=type_hints["ext_vars"])
            check_type(argname="argument libs", value=libs, expected_type=type_hints["libs"])
            check_type(argname="argument tlas", value=tlas, expected_type=type_hints["tlas"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if ext_vars is not None:
            self._values["ext_vars"] = ext_vars
        if libs is not None:
            self._values["libs"] = libs
        if tlas is not None:
            self._values["tlas"] = tlas

    @builtins.property
    def ext_vars(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourceDirectoryJsonnetExtVars"]]:
        '''ExtVars is a list of Jsonnet External Variables.

        :schema: ApplicationOperationSyncSourceDirectoryJsonnet#extVars
        '''
        result = self._values.get("ext_vars")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourceDirectoryJsonnetExtVars"]], result)

    @builtins.property
    def libs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Additional library search dirs.

        :schema: ApplicationOperationSyncSourceDirectoryJsonnet#libs
        '''
        result = self._values.get("libs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def tlas(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourceDirectoryJsonnetTlas"]]:
        '''TLAS is a list of Jsonnet Top-level Arguments.

        :schema: ApplicationOperationSyncSourceDirectoryJsonnet#tlas
        '''
        result = self._values.get("tlas")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourceDirectoryJsonnetTlas"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceDirectoryJsonnet(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceDirectoryJsonnetExtVars",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value", "code": "code"},
)
class ApplicationOperationSyncSourceDirectoryJsonnetExtVars:
    def __init__(
        self,
        *,
        name: builtins.str,
        value: builtins.str,
        code: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''JsonnetVar represents a variable to be passed to jsonnet during manifest generation.

        :param name: 
        :param value: 
        :param code: 

        :schema: ApplicationOperationSyncSourceDirectoryJsonnetExtVars
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__966c0a7acfd38fe0dce9dbf0d8bdd38f51b40bc26789ce769399c983ad046f32)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument code", value=code, expected_type=type_hints["code"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }
        if code is not None:
            self._values["code"] = code

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncSourceDirectoryJsonnetExtVars#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncSourceDirectoryJsonnetExtVars#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def code(self) -> typing.Optional[builtins.bool]:
        '''
        :schema: ApplicationOperationSyncSourceDirectoryJsonnetExtVars#code
        '''
        result = self._values.get("code")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceDirectoryJsonnetExtVars(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceDirectoryJsonnetTlas",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value", "code": "code"},
)
class ApplicationOperationSyncSourceDirectoryJsonnetTlas:
    def __init__(
        self,
        *,
        name: builtins.str,
        value: builtins.str,
        code: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''JsonnetVar represents a variable to be passed to jsonnet during manifest generation.

        :param name: 
        :param value: 
        :param code: 

        :schema: ApplicationOperationSyncSourceDirectoryJsonnetTlas
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c0c87bea537ea3fd2aa5b34f35cbe7f666f5d15a2ddc3b382248bc32490d4832)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument code", value=code, expected_type=type_hints["code"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }
        if code is not None:
            self._values["code"] = code

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncSourceDirectoryJsonnetTlas#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncSourceDirectoryJsonnetTlas#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def code(self) -> typing.Optional[builtins.bool]:
        '''
        :schema: ApplicationOperationSyncSourceDirectoryJsonnetTlas#code
        '''
        result = self._values.get("code")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceDirectoryJsonnetTlas(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceHelm",
    jsii_struct_bases=[],
    name_mapping={
        "api_versions": "apiVersions",
        "file_parameters": "fileParameters",
        "ignore_missing_value_files": "ignoreMissingValueFiles",
        "kube_version": "kubeVersion",
        "namespace": "namespace",
        "parameters": "parameters",
        "pass_credentials": "passCredentials",
        "release_name": "releaseName",
        "skip_crds": "skipCrds",
        "skip_schema_validation": "skipSchemaValidation",
        "skip_tests": "skipTests",
        "value_files": "valueFiles",
        "values": "values",
        "values_object": "valuesObject",
        "version": "version",
    },
)
class ApplicationOperationSyncSourceHelm:
    def __init__(
        self,
        *,
        api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
        file_parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourceHelmFileParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_missing_value_files: typing.Optional[builtins.bool] = None,
        kube_version: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourceHelmParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
        pass_credentials: typing.Optional[builtins.bool] = None,
        release_name: typing.Optional[builtins.str] = None,
        skip_crds: typing.Optional[builtins.bool] = None,
        skip_schema_validation: typing.Optional[builtins.bool] = None,
        skip_tests: typing.Optional[builtins.bool] = None,
        value_files: typing.Optional[typing.Sequence[builtins.str]] = None,
        values: typing.Optional[builtins.str] = None,
        values_object: typing.Any = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Helm holds helm specific options.

        :param api_versions: APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests. By default, Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.
        :param file_parameters: FileParameters are file parameters to the helm template.
        :param ignore_missing_value_files: IgnoreMissingValueFiles prevents helm template from failing when valueFiles do not exist locally by not appending them to helm template --values.
        :param kube_version: KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests. By default, Argo CD uses the Kubernetes version of the target cluster.
        :param namespace: Namespace is an optional namespace to template with. If left empty, defaults to the app's destination namespace.
        :param parameters: Parameters is a list of Helm parameters which are passed to the helm template command upon manifest generation.
        :param pass_credentials: PassCredentials pass credentials to all domains (Helm's --pass-credentials).
        :param release_name: ReleaseName is the Helm release name to use. If omitted it will use the application name
        :param skip_crds: SkipCrds skips custom resource definition installation step (Helm's --skip-crds).
        :param skip_schema_validation: SkipSchemaValidation skips JSON schema validation (Helm's --skip-schema-validation).
        :param skip_tests: SkipTests skips test manifest installation step (Helm's --skip-tests).
        :param value_files: ValuesFiles is a list of Helm value files to use when generating a template.
        :param values: Values specifies Helm values to be passed to helm template, typically defined as a block. ValuesObject takes precedence over Values, so use one or the other.
        :param values_object: ValuesObject specifies Helm values to be passed to helm template, defined as a map. This takes precedence over Values.
        :param version: Version is the Helm version to use for templating ("3").

        :schema: ApplicationOperationSyncSourceHelm
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b386c667b68ec553767e009262cc57f6b9dd41e43536fc3d79443da816b4ae76)
            check_type(argname="argument api_versions", value=api_versions, expected_type=type_hints["api_versions"])
            check_type(argname="argument file_parameters", value=file_parameters, expected_type=type_hints["file_parameters"])
            check_type(argname="argument ignore_missing_value_files", value=ignore_missing_value_files, expected_type=type_hints["ignore_missing_value_files"])
            check_type(argname="argument kube_version", value=kube_version, expected_type=type_hints["kube_version"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
            check_type(argname="argument pass_credentials", value=pass_credentials, expected_type=type_hints["pass_credentials"])
            check_type(argname="argument release_name", value=release_name, expected_type=type_hints["release_name"])
            check_type(argname="argument skip_crds", value=skip_crds, expected_type=type_hints["skip_crds"])
            check_type(argname="argument skip_schema_validation", value=skip_schema_validation, expected_type=type_hints["skip_schema_validation"])
            check_type(argname="argument skip_tests", value=skip_tests, expected_type=type_hints["skip_tests"])
            check_type(argname="argument value_files", value=value_files, expected_type=type_hints["value_files"])
            check_type(argname="argument values", value=values, expected_type=type_hints["values"])
            check_type(argname="argument values_object", value=values_object, expected_type=type_hints["values_object"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_versions is not None:
            self._values["api_versions"] = api_versions
        if file_parameters is not None:
            self._values["file_parameters"] = file_parameters
        if ignore_missing_value_files is not None:
            self._values["ignore_missing_value_files"] = ignore_missing_value_files
        if kube_version is not None:
            self._values["kube_version"] = kube_version
        if namespace is not None:
            self._values["namespace"] = namespace
        if parameters is not None:
            self._values["parameters"] = parameters
        if pass_credentials is not None:
            self._values["pass_credentials"] = pass_credentials
        if release_name is not None:
            self._values["release_name"] = release_name
        if skip_crds is not None:
            self._values["skip_crds"] = skip_crds
        if skip_schema_validation is not None:
            self._values["skip_schema_validation"] = skip_schema_validation
        if skip_tests is not None:
            self._values["skip_tests"] = skip_tests
        if value_files is not None:
            self._values["value_files"] = value_files
        if values is not None:
            self._values["values"] = values
        if values_object is not None:
            self._values["values_object"] = values_object
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def api_versions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests.

        By default,
        Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.

        :schema: ApplicationOperationSyncSourceHelm#apiVersions
        '''
        result = self._values.get("api_versions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def file_parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourceHelmFileParameters"]]:
        '''FileParameters are file parameters to the helm template.

        :schema: ApplicationOperationSyncSourceHelm#fileParameters
        '''
        result = self._values.get("file_parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourceHelmFileParameters"]], result)

    @builtins.property
    def ignore_missing_value_files(self) -> typing.Optional[builtins.bool]:
        '''IgnoreMissingValueFiles prevents helm template from failing when valueFiles do not exist locally by not appending them to helm template --values.

        :schema: ApplicationOperationSyncSourceHelm#ignoreMissingValueFiles
        '''
        result = self._values.get("ignore_missing_value_files")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def kube_version(self) -> typing.Optional[builtins.str]:
        '''KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests.

        By default, Argo CD
        uses the Kubernetes version of the target cluster.

        :schema: ApplicationOperationSyncSourceHelm#kubeVersion
        '''
        result = self._values.get("kube_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace is an optional namespace to template with.

        If left empty, defaults to the app's destination namespace.

        :schema: ApplicationOperationSyncSourceHelm#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourceHelmParameters"]]:
        '''Parameters is a list of Helm parameters which are passed to the helm template command upon manifest generation.

        :schema: ApplicationOperationSyncSourceHelm#parameters
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourceHelmParameters"]], result)

    @builtins.property
    def pass_credentials(self) -> typing.Optional[builtins.bool]:
        '''PassCredentials pass credentials to all domains (Helm's --pass-credentials).

        :schema: ApplicationOperationSyncSourceHelm#passCredentials
        '''
        result = self._values.get("pass_credentials")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_name(self) -> typing.Optional[builtins.str]:
        '''ReleaseName is the Helm release name to use.

        If omitted it will use the application name

        :schema: ApplicationOperationSyncSourceHelm#releaseName
        '''
        result = self._values.get("release_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def skip_crds(self) -> typing.Optional[builtins.bool]:
        '''SkipCrds skips custom resource definition installation step (Helm's --skip-crds).

        :schema: ApplicationOperationSyncSourceHelm#skipCrds
        '''
        result = self._values.get("skip_crds")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip_schema_validation(self) -> typing.Optional[builtins.bool]:
        '''SkipSchemaValidation skips JSON schema validation (Helm's --skip-schema-validation).

        :schema: ApplicationOperationSyncSourceHelm#skipSchemaValidation
        '''
        result = self._values.get("skip_schema_validation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip_tests(self) -> typing.Optional[builtins.bool]:
        '''SkipTests skips test manifest installation step (Helm's --skip-tests).

        :schema: ApplicationOperationSyncSourceHelm#skipTests
        '''
        result = self._values.get("skip_tests")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def value_files(self) -> typing.Optional[typing.List[builtins.str]]:
        '''ValuesFiles is a list of Helm value files to use when generating a template.

        :schema: ApplicationOperationSyncSourceHelm#valueFiles
        '''
        result = self._values.get("value_files")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def values(self) -> typing.Optional[builtins.str]:
        '''Values specifies Helm values to be passed to helm template, typically defined as a block.

        ValuesObject takes precedence over Values, so use one or the other.

        :schema: ApplicationOperationSyncSourceHelm#values
        '''
        result = self._values.get("values")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def values_object(self) -> typing.Any:
        '''ValuesObject specifies Helm values to be passed to helm template, defined as a map.

        This takes precedence over Values.

        :schema: ApplicationOperationSyncSourceHelm#valuesObject
        '''
        result = self._values.get("values_object")
        return typing.cast(typing.Any, result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version is the Helm version to use for templating ("3").

        :schema: ApplicationOperationSyncSourceHelm#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceHelm(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceHelmFileParameters",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "path": "path"},
)
class ApplicationOperationSyncSourceHelmFileParameters:
    def __init__(
        self,
        *,
        name: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HelmFileParameter is a file parameter that's passed to helm template during manifest generation.

        :param name: Name is the name of the Helm parameter.
        :param path: Path is the path to the file containing the values for the Helm parameter.

        :schema: ApplicationOperationSyncSourceHelmFileParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bda8f2463180d72c0afdd472e8d7562b7f94b54167bbff1ef898c73de3218c9b)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if name is not None:
            self._values["name"] = name
        if path is not None:
            self._values["path"] = path

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name of the Helm parameter.

        :schema: ApplicationOperationSyncSourceHelmFileParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Path is the path to the file containing the values for the Helm parameter.

        :schema: ApplicationOperationSyncSourceHelmFileParameters#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceHelmFileParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceHelmParameters",
    jsii_struct_bases=[],
    name_mapping={"force_string": "forceString", "name": "name", "value": "value"},
)
class ApplicationOperationSyncSourceHelmParameters:
    def __init__(
        self,
        *,
        force_string: typing.Optional[builtins.bool] = None,
        name: typing.Optional[builtins.str] = None,
        value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HelmParameter is a parameter that's passed to helm template during manifest generation.

        :param force_string: ForceString determines whether to tell Helm to interpret booleans and numbers as strings.
        :param name: Name is the name of the Helm parameter.
        :param value: Value is the value for the Helm parameter.

        :schema: ApplicationOperationSyncSourceHelmParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ac77b224717d4ca6dae0e47a49730c4a858ab4ae9672d7ab36360686bb3442d8)
            check_type(argname="argument force_string", value=force_string, expected_type=type_hints["force_string"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if force_string is not None:
            self._values["force_string"] = force_string
        if name is not None:
            self._values["name"] = name
        if value is not None:
            self._values["value"] = value

    @builtins.property
    def force_string(self) -> typing.Optional[builtins.bool]:
        '''ForceString determines whether to tell Helm to interpret booleans and numbers as strings.

        :schema: ApplicationOperationSyncSourceHelmParameters#forceString
        '''
        result = self._values.get("force_string")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name of the Helm parameter.

        :schema: ApplicationOperationSyncSourceHelmParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def value(self) -> typing.Optional[builtins.str]:
        '''Value is the value for the Helm parameter.

        :schema: ApplicationOperationSyncSourceHelmParameters#value
        '''
        result = self._values.get("value")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceHelmParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceKustomize",
    jsii_struct_bases=[],
    name_mapping={
        "api_versions": "apiVersions",
        "common_annotations": "commonAnnotations",
        "common_annotations_envsubst": "commonAnnotationsEnvsubst",
        "common_labels": "commonLabels",
        "components": "components",
        "force_common_annotations": "forceCommonAnnotations",
        "force_common_labels": "forceCommonLabels",
        "ignore_missing_components": "ignoreMissingComponents",
        "images": "images",
        "kube_version": "kubeVersion",
        "label_include_templates": "labelIncludeTemplates",
        "label_without_selector": "labelWithoutSelector",
        "name_prefix": "namePrefix",
        "namespace": "namespace",
        "name_suffix": "nameSuffix",
        "patches": "patches",
        "replicas": "replicas",
        "version": "version",
    },
)
class ApplicationOperationSyncSourceKustomize:
    def __init__(
        self,
        *,
        api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
        common_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        common_annotations_envsubst: typing.Optional[builtins.bool] = None,
        common_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        components: typing.Optional[typing.Sequence[builtins.str]] = None,
        force_common_annotations: typing.Optional[builtins.bool] = None,
        force_common_labels: typing.Optional[builtins.bool] = None,
        ignore_missing_components: typing.Optional[builtins.bool] = None,
        images: typing.Optional[typing.Sequence[builtins.str]] = None,
        kube_version: typing.Optional[builtins.str] = None,
        label_include_templates: typing.Optional[builtins.bool] = None,
        label_without_selector: typing.Optional[builtins.bool] = None,
        name_prefix: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        name_suffix: typing.Optional[builtins.str] = None,
        patches: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourceKustomizePatches", typing.Dict[builtins.str, typing.Any]]]] = None,
        replicas: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourceKustomizeReplicas", typing.Dict[builtins.str, typing.Any]]]] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Kustomize holds kustomize specific options.

        :param api_versions: APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests. By default, Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.
        :param common_annotations: CommonAnnotations is a list of additional annotations to add to rendered manifests.
        :param common_annotations_envsubst: CommonAnnotationsEnvsubst specifies whether to apply env variables substitution for annotation values.
        :param common_labels: CommonLabels is a list of additional labels to add to rendered manifests.
        :param components: Components specifies a list of kustomize components to add to the kustomization before building.
        :param force_common_annotations: ForceCommonAnnotations specifies whether to force applying common annotations to resources for Kustomize apps.
        :param force_common_labels: ForceCommonLabels specifies whether to force applying common labels to resources for Kustomize apps.
        :param ignore_missing_components: IgnoreMissingComponents prevents kustomize from failing when components do not exist locally by not appending them to kustomization file.
        :param images: Images is a list of Kustomize image override specifications.
        :param kube_version: KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests. By default, Argo CD uses the Kubernetes version of the target cluster.
        :param label_include_templates: LabelIncludeTemplates specifies whether to apply common labels to resource templates or not.
        :param label_without_selector: LabelWithoutSelector specifies whether to apply common labels to resource selectors or not.
        :param name_prefix: NamePrefix is a prefix appended to resources for Kustomize apps.
        :param namespace: Namespace sets the namespace that Kustomize adds to all resources.
        :param name_suffix: NameSuffix is a suffix appended to resources for Kustomize apps.
        :param patches: Patches is a list of Kustomize patches.
        :param replicas: Replicas is a list of Kustomize Replicas override specifications.
        :param version: Version controls which version of Kustomize to use for rendering manifests.

        :schema: ApplicationOperationSyncSourceKustomize
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2b738b3c037af039c4d26e237b22edf72e087f17f848436770e7d91aa35803be)
            check_type(argname="argument api_versions", value=api_versions, expected_type=type_hints["api_versions"])
            check_type(argname="argument common_annotations", value=common_annotations, expected_type=type_hints["common_annotations"])
            check_type(argname="argument common_annotations_envsubst", value=common_annotations_envsubst, expected_type=type_hints["common_annotations_envsubst"])
            check_type(argname="argument common_labels", value=common_labels, expected_type=type_hints["common_labels"])
            check_type(argname="argument components", value=components, expected_type=type_hints["components"])
            check_type(argname="argument force_common_annotations", value=force_common_annotations, expected_type=type_hints["force_common_annotations"])
            check_type(argname="argument force_common_labels", value=force_common_labels, expected_type=type_hints["force_common_labels"])
            check_type(argname="argument ignore_missing_components", value=ignore_missing_components, expected_type=type_hints["ignore_missing_components"])
            check_type(argname="argument images", value=images, expected_type=type_hints["images"])
            check_type(argname="argument kube_version", value=kube_version, expected_type=type_hints["kube_version"])
            check_type(argname="argument label_include_templates", value=label_include_templates, expected_type=type_hints["label_include_templates"])
            check_type(argname="argument label_without_selector", value=label_without_selector, expected_type=type_hints["label_without_selector"])
            check_type(argname="argument name_prefix", value=name_prefix, expected_type=type_hints["name_prefix"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument name_suffix", value=name_suffix, expected_type=type_hints["name_suffix"])
            check_type(argname="argument patches", value=patches, expected_type=type_hints["patches"])
            check_type(argname="argument replicas", value=replicas, expected_type=type_hints["replicas"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_versions is not None:
            self._values["api_versions"] = api_versions
        if common_annotations is not None:
            self._values["common_annotations"] = common_annotations
        if common_annotations_envsubst is not None:
            self._values["common_annotations_envsubst"] = common_annotations_envsubst
        if common_labels is not None:
            self._values["common_labels"] = common_labels
        if components is not None:
            self._values["components"] = components
        if force_common_annotations is not None:
            self._values["force_common_annotations"] = force_common_annotations
        if force_common_labels is not None:
            self._values["force_common_labels"] = force_common_labels
        if ignore_missing_components is not None:
            self._values["ignore_missing_components"] = ignore_missing_components
        if images is not None:
            self._values["images"] = images
        if kube_version is not None:
            self._values["kube_version"] = kube_version
        if label_include_templates is not None:
            self._values["label_include_templates"] = label_include_templates
        if label_without_selector is not None:
            self._values["label_without_selector"] = label_without_selector
        if name_prefix is not None:
            self._values["name_prefix"] = name_prefix
        if namespace is not None:
            self._values["namespace"] = namespace
        if name_suffix is not None:
            self._values["name_suffix"] = name_suffix
        if patches is not None:
            self._values["patches"] = patches
        if replicas is not None:
            self._values["replicas"] = replicas
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def api_versions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests.

        By default,
        Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.

        :schema: ApplicationOperationSyncSourceKustomize#apiVersions
        '''
        result = self._values.get("api_versions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def common_annotations(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''CommonAnnotations is a list of additional annotations to add to rendered manifests.

        :schema: ApplicationOperationSyncSourceKustomize#commonAnnotations
        '''
        result = self._values.get("common_annotations")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def common_annotations_envsubst(self) -> typing.Optional[builtins.bool]:
        '''CommonAnnotationsEnvsubst specifies whether to apply env variables substitution for annotation values.

        :schema: ApplicationOperationSyncSourceKustomize#commonAnnotationsEnvsubst
        '''
        result = self._values.get("common_annotations_envsubst")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def common_labels(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''CommonLabels is a list of additional labels to add to rendered manifests.

        :schema: ApplicationOperationSyncSourceKustomize#commonLabels
        '''
        result = self._values.get("common_labels")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def components(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Components specifies a list of kustomize components to add to the kustomization before building.

        :schema: ApplicationOperationSyncSourceKustomize#components
        '''
        result = self._values.get("components")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def force_common_annotations(self) -> typing.Optional[builtins.bool]:
        '''ForceCommonAnnotations specifies whether to force applying common annotations to resources for Kustomize apps.

        :schema: ApplicationOperationSyncSourceKustomize#forceCommonAnnotations
        '''
        result = self._values.get("force_common_annotations")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def force_common_labels(self) -> typing.Optional[builtins.bool]:
        '''ForceCommonLabels specifies whether to force applying common labels to resources for Kustomize apps.

        :schema: ApplicationOperationSyncSourceKustomize#forceCommonLabels
        '''
        result = self._values.get("force_common_labels")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def ignore_missing_components(self) -> typing.Optional[builtins.bool]:
        '''IgnoreMissingComponents prevents kustomize from failing when components do not exist locally by not appending them to kustomization file.

        :schema: ApplicationOperationSyncSourceKustomize#ignoreMissingComponents
        '''
        result = self._values.get("ignore_missing_components")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def images(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Images is a list of Kustomize image override specifications.

        :schema: ApplicationOperationSyncSourceKustomize#images
        '''
        result = self._values.get("images")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def kube_version(self) -> typing.Optional[builtins.str]:
        '''KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests.

        By default, Argo CD
        uses the Kubernetes version of the target cluster.

        :schema: ApplicationOperationSyncSourceKustomize#kubeVersion
        '''
        result = self._values.get("kube_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def label_include_templates(self) -> typing.Optional[builtins.bool]:
        '''LabelIncludeTemplates specifies whether to apply common labels to resource templates or not.

        :schema: ApplicationOperationSyncSourceKustomize#labelIncludeTemplates
        '''
        result = self._values.get("label_include_templates")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def label_without_selector(self) -> typing.Optional[builtins.bool]:
        '''LabelWithoutSelector specifies whether to apply common labels to resource selectors or not.

        :schema: ApplicationOperationSyncSourceKustomize#labelWithoutSelector
        '''
        result = self._values.get("label_without_selector")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def name_prefix(self) -> typing.Optional[builtins.str]:
        '''NamePrefix is a prefix appended to resources for Kustomize apps.

        :schema: ApplicationOperationSyncSourceKustomize#namePrefix
        '''
        result = self._values.get("name_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace sets the namespace that Kustomize adds to all resources.

        :schema: ApplicationOperationSyncSourceKustomize#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name_suffix(self) -> typing.Optional[builtins.str]:
        '''NameSuffix is a suffix appended to resources for Kustomize apps.

        :schema: ApplicationOperationSyncSourceKustomize#nameSuffix
        '''
        result = self._values.get("name_suffix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def patches(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourceKustomizePatches"]]:
        '''Patches is a list of Kustomize patches.

        :schema: ApplicationOperationSyncSourceKustomize#patches
        '''
        result = self._values.get("patches")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourceKustomizePatches"]], result)

    @builtins.property
    def replicas(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourceKustomizeReplicas"]]:
        '''Replicas is a list of Kustomize Replicas override specifications.

        :schema: ApplicationOperationSyncSourceKustomize#replicas
        '''
        result = self._values.get("replicas")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourceKustomizeReplicas"]], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version controls which version of Kustomize to use for rendering manifests.

        :schema: ApplicationOperationSyncSourceKustomize#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceKustomize(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceKustomizePatches",
    jsii_struct_bases=[],
    name_mapping={
        "options": "options",
        "patch": "patch",
        "path": "path",
        "target": "target",
    },
)
class ApplicationOperationSyncSourceKustomizePatches:
    def __init__(
        self,
        *,
        options: typing.Optional[typing.Mapping[builtins.str, builtins.bool]] = None,
        patch: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        target: typing.Optional[typing.Union["ApplicationOperationSyncSourceKustomizePatchesTarget", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param options: 
        :param patch: 
        :param path: 
        :param target: 

        :schema: ApplicationOperationSyncSourceKustomizePatches
        '''
        if isinstance(target, dict):
            target = ApplicationOperationSyncSourceKustomizePatchesTarget(**target)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__403d98dbeb14f0d44b70e8177847cac9923ac145b2bedcf54c929d57c91d07f3)
            check_type(argname="argument options", value=options, expected_type=type_hints["options"])
            check_type(argname="argument patch", value=patch, expected_type=type_hints["patch"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if options is not None:
            self._values["options"] = options
        if patch is not None:
            self._values["patch"] = patch
        if path is not None:
            self._values["path"] = path
        if target is not None:
            self._values["target"] = target

    @builtins.property
    def options(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.bool]]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatches#options
        '''
        result = self._values.get("options")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.bool]], result)

    @builtins.property
    def patch(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatches#patch
        '''
        result = self._values.get("patch")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatches#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target(
        self,
    ) -> typing.Optional["ApplicationOperationSyncSourceKustomizePatchesTarget"]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatches#target
        '''
        result = self._values.get("target")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourceKustomizePatchesTarget"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceKustomizePatches(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceKustomizePatchesTarget",
    jsii_struct_bases=[],
    name_mapping={
        "annotation_selector": "annotationSelector",
        "group": "group",
        "kind": "kind",
        "label_selector": "labelSelector",
        "name": "name",
        "namespace": "namespace",
        "version": "version",
    },
)
class ApplicationOperationSyncSourceKustomizePatchesTarget:
    def __init__(
        self,
        *,
        annotation_selector: typing.Optional[builtins.str] = None,
        group: typing.Optional[builtins.str] = None,
        kind: typing.Optional[builtins.str] = None,
        label_selector: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param annotation_selector: 
        :param group: 
        :param kind: 
        :param label_selector: 
        :param name: 
        :param namespace: 
        :param version: 

        :schema: ApplicationOperationSyncSourceKustomizePatchesTarget
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__45dc4ffc9c41609070e18c4045a1fd3469f2771b2f5a70d08b8029fc6a090036)
            check_type(argname="argument annotation_selector", value=annotation_selector, expected_type=type_hints["annotation_selector"])
            check_type(argname="argument group", value=group, expected_type=type_hints["group"])
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument label_selector", value=label_selector, expected_type=type_hints["label_selector"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if annotation_selector is not None:
            self._values["annotation_selector"] = annotation_selector
        if group is not None:
            self._values["group"] = group
        if kind is not None:
            self._values["kind"] = kind
        if label_selector is not None:
            self._values["label_selector"] = label_selector
        if name is not None:
            self._values["name"] = name
        if namespace is not None:
            self._values["namespace"] = namespace
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def annotation_selector(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatchesTarget#annotationSelector
        '''
        result = self._values.get("annotation_selector")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def group(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatchesTarget#group
        '''
        result = self._values.get("group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def kind(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatchesTarget#kind
        '''
        result = self._values.get("kind")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def label_selector(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatchesTarget#labelSelector
        '''
        result = self._values.get("label_selector")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatchesTarget#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatchesTarget#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourceKustomizePatchesTarget#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceKustomizePatchesTarget(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourceKustomizeReplicas",
    jsii_struct_bases=[],
    name_mapping={"count": "count", "name": "name"},
)
class ApplicationOperationSyncSourceKustomizeReplicas:
    def __init__(
        self,
        *,
        count: "ApplicationOperationSyncSourceKustomizeReplicasCount",
        name: builtins.str,
    ) -> None:
        '''
        :param count: Number of replicas.
        :param name: Name of Deployment or StatefulSet.

        :schema: ApplicationOperationSyncSourceKustomizeReplicas
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5bcfa17d48c31956a1583c4b8e33c2236f203e85774d1972c956f7e4d0408c47)
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "count": count,
            "name": name,
        }

    @builtins.property
    def count(self) -> "ApplicationOperationSyncSourceKustomizeReplicasCount":
        '''Number of replicas.

        :schema: ApplicationOperationSyncSourceKustomizeReplicas#count
        '''
        result = self._values.get("count")
        assert result is not None, "Required property 'count' is missing"
        return typing.cast("ApplicationOperationSyncSourceKustomizeReplicasCount", result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of Deployment or StatefulSet.

        :schema: ApplicationOperationSyncSourceKustomizeReplicas#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourceKustomizeReplicas(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ApplicationOperationSyncSourceKustomizeReplicasCount(
    metaclass=jsii.JSIIMeta,
    jsii_type="ioargoproj.ApplicationOperationSyncSourceKustomizeReplicasCount",
):
    '''Number of replicas.

    :schema: ApplicationOperationSyncSourceKustomizeReplicasCount
    '''

    @jsii.member(jsii_name="fromNumber")
    @builtins.classmethod
    def from_number(
        cls,
        value: jsii.Number,
    ) -> "ApplicationOperationSyncSourceKustomizeReplicasCount":
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__353ac407776b154158bf4858074912a6ab4bb0e6505180220b0a9389af131e28)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast("ApplicationOperationSyncSourceKustomizeReplicasCount", jsii.sinvoke(cls, "fromNumber", [value]))

    @jsii.member(jsii_name="fromString")
    @builtins.classmethod
    def from_string(
        cls,
        value: builtins.str,
    ) -> "ApplicationOperationSyncSourceKustomizeReplicasCount":
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0396193d2a74e325951a6b23c7478a300a48ae901e7b6dcdd57ee2f9ef65e360)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast("ApplicationOperationSyncSourceKustomizeReplicasCount", jsii.sinvoke(cls, "fromString", [value]))

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(self) -> typing.Union[builtins.str, jsii.Number]:
        return typing.cast(typing.Union[builtins.str, jsii.Number], jsii.get(self, "value"))


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcePlugin",
    jsii_struct_bases=[],
    name_mapping={"env": "env", "name": "name", "parameters": "parameters"},
)
class ApplicationOperationSyncSourcePlugin:
    def __init__(
        self,
        *,
        env: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcePluginEnv", typing.Dict[builtins.str, typing.Any]]]] = None,
        name: typing.Optional[builtins.str] = None,
        parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcePluginParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Plugin holds config management plugin specific options.

        :param env: Env is a list of environment variable entries.
        :param name: 
        :param parameters: 

        :schema: ApplicationOperationSyncSourcePlugin
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b963da857103b74fb6dd9321f58bbec9ef78c44c0c7c7001fc7a5a40a45ab57e)
            check_type(argname="argument env", value=env, expected_type=type_hints["env"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if env is not None:
            self._values["env"] = env
        if name is not None:
            self._values["name"] = name
        if parameters is not None:
            self._values["parameters"] = parameters

    @builtins.property
    def env(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcePluginEnv"]]:
        '''Env is a list of environment variable entries.

        :schema: ApplicationOperationSyncSourcePlugin#env
        '''
        result = self._values.get("env")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcePluginEnv"]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcePlugin#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcePluginParameters"]]:
        '''
        :schema: ApplicationOperationSyncSourcePlugin#parameters
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcePluginParameters"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcePlugin(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcePluginEnv",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value"},
)
class ApplicationOperationSyncSourcePluginEnv:
    def __init__(self, *, name: builtins.str, value: builtins.str) -> None:
        '''EnvEntry represents an entry in the application's environment.

        :param name: Name is the name of the variable, usually expressed in uppercase.
        :param value: Value is the value of the variable.

        :schema: ApplicationOperationSyncSourcePluginEnv
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bac56bca7082a809be909907326178a0ef4bcd363c89b646e42378bbe3b80e2c)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''Name is the name of the variable, usually expressed in uppercase.

        :schema: ApplicationOperationSyncSourcePluginEnv#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''Value is the value of the variable.

        :schema: ApplicationOperationSyncSourcePluginEnv#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcePluginEnv(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcePluginParameters",
    jsii_struct_bases=[],
    name_mapping={"array": "array", "map": "map", "name": "name", "string": "string"},
)
class ApplicationOperationSyncSourcePluginParameters:
    def __init__(
        self,
        *,
        array: typing.Optional[typing.Sequence[builtins.str]] = None,
        map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        string: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param array: Array is the value of an array type parameter.
        :param map: Map is the value of a map type parameter.
        :param name: Name is the name identifying a parameter.
        :param string: String_ is the value of a string type parameter.

        :schema: ApplicationOperationSyncSourcePluginParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7720bb9e4d0879b72177070fac6d572303d14b0a3dfca7a0b6acb7d254940def)
            check_type(argname="argument array", value=array, expected_type=type_hints["array"])
            check_type(argname="argument map", value=map, expected_type=type_hints["map"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument string", value=string, expected_type=type_hints["string"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if array is not None:
            self._values["array"] = array
        if map is not None:
            self._values["map"] = map
        if name is not None:
            self._values["name"] = name
        if string is not None:
            self._values["string"] = string

    @builtins.property
    def array(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array is the value of an array type parameter.

        :schema: ApplicationOperationSyncSourcePluginParameters#array
        '''
        result = self._values.get("array")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def map(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Map is the value of a map type parameter.

        :schema: ApplicationOperationSyncSourcePluginParameters#map
        '''
        result = self._values.get("map")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name identifying a parameter.

        :schema: ApplicationOperationSyncSourcePluginParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def string(self) -> typing.Optional[builtins.str]:
        '''String_ is the value of a string type parameter.

        :schema: ApplicationOperationSyncSourcePluginParameters#string
        '''
        result = self._values.get("string")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcePluginParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSources",
    jsii_struct_bases=[],
    name_mapping={
        "repo_url": "repoUrl",
        "chart": "chart",
        "directory": "directory",
        "helm": "helm",
        "kustomize": "kustomize",
        "name": "name",
        "path": "path",
        "plugin": "plugin",
        "ref": "ref",
        "target_revision": "targetRevision",
    },
)
class ApplicationOperationSyncSources:
    def __init__(
        self,
        *,
        repo_url: builtins.str,
        chart: typing.Optional[builtins.str] = None,
        directory: typing.Optional[typing.Union["ApplicationOperationSyncSourcesDirectory", typing.Dict[builtins.str, typing.Any]]] = None,
        helm: typing.Optional[typing.Union["ApplicationOperationSyncSourcesHelm", typing.Dict[builtins.str, typing.Any]]] = None,
        kustomize: typing.Optional[typing.Union["ApplicationOperationSyncSourcesKustomize", typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        plugin: typing.Optional[typing.Union["ApplicationOperationSyncSourcesPlugin", typing.Dict[builtins.str, typing.Any]]] = None,
        ref: typing.Optional[builtins.str] = None,
        target_revision: typing.Optional[builtins.str] = None,
    ) -> None:
        '''ApplicationSource contains all required information about the source of an application.

        :param repo_url: RepoURL is the URL to the repository (Git or Helm) that contains the application manifests.
        :param chart: Chart is a Helm chart name, and must be specified for applications sourced from a Helm repo.
        :param directory: Directory holds path/directory specific options.
        :param helm: Helm holds helm specific options.
        :param kustomize: Kustomize holds kustomize specific options.
        :param name: Name is used to refer to a source and is displayed in the UI. It is used in multi-source Applications.
        :param path: Path is a directory path within the Git repository, and is only valid for applications sourced from Git.
        :param plugin: Plugin holds config management plugin specific options.
        :param ref: Ref is reference to another source within sources field. This field will not be used if used with a ``source`` tag.
        :param target_revision: TargetRevision defines the revision of the source to sync the application to. In case of Git, this can be commit, tag, or branch. If omitted, will equal to HEAD. In case of Helm, this is a semver tag for the Chart's version.

        :schema: ApplicationOperationSyncSources
        '''
        if isinstance(directory, dict):
            directory = ApplicationOperationSyncSourcesDirectory(**directory)
        if isinstance(helm, dict):
            helm = ApplicationOperationSyncSourcesHelm(**helm)
        if isinstance(kustomize, dict):
            kustomize = ApplicationOperationSyncSourcesKustomize(**kustomize)
        if isinstance(plugin, dict):
            plugin = ApplicationOperationSyncSourcesPlugin(**plugin)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__131a3b605137deb720d23b45b3ff58347f2c9100e00540ecdfef615ebf73e4ca)
            check_type(argname="argument repo_url", value=repo_url, expected_type=type_hints["repo_url"])
            check_type(argname="argument chart", value=chart, expected_type=type_hints["chart"])
            check_type(argname="argument directory", value=directory, expected_type=type_hints["directory"])
            check_type(argname="argument helm", value=helm, expected_type=type_hints["helm"])
            check_type(argname="argument kustomize", value=kustomize, expected_type=type_hints["kustomize"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument plugin", value=plugin, expected_type=type_hints["plugin"])
            check_type(argname="argument ref", value=ref, expected_type=type_hints["ref"])
            check_type(argname="argument target_revision", value=target_revision, expected_type=type_hints["target_revision"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "repo_url": repo_url,
        }
        if chart is not None:
            self._values["chart"] = chart
        if directory is not None:
            self._values["directory"] = directory
        if helm is not None:
            self._values["helm"] = helm
        if kustomize is not None:
            self._values["kustomize"] = kustomize
        if name is not None:
            self._values["name"] = name
        if path is not None:
            self._values["path"] = path
        if plugin is not None:
            self._values["plugin"] = plugin
        if ref is not None:
            self._values["ref"] = ref
        if target_revision is not None:
            self._values["target_revision"] = target_revision

    @builtins.property
    def repo_url(self) -> builtins.str:
        '''RepoURL is the URL to the repository (Git or Helm) that contains the application manifests.

        :schema: ApplicationOperationSyncSources#repoURL
        '''
        result = self._values.get("repo_url")
        assert result is not None, "Required property 'repo_url' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def chart(self) -> typing.Optional[builtins.str]:
        '''Chart is a Helm chart name, and must be specified for applications sourced from a Helm repo.

        :schema: ApplicationOperationSyncSources#chart
        '''
        result = self._values.get("chart")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def directory(self) -> typing.Optional["ApplicationOperationSyncSourcesDirectory"]:
        '''Directory holds path/directory specific options.

        :schema: ApplicationOperationSyncSources#directory
        '''
        result = self._values.get("directory")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourcesDirectory"], result)

    @builtins.property
    def helm(self) -> typing.Optional["ApplicationOperationSyncSourcesHelm"]:
        '''Helm holds helm specific options.

        :schema: ApplicationOperationSyncSources#helm
        '''
        result = self._values.get("helm")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourcesHelm"], result)

    @builtins.property
    def kustomize(self) -> typing.Optional["ApplicationOperationSyncSourcesKustomize"]:
        '''Kustomize holds kustomize specific options.

        :schema: ApplicationOperationSyncSources#kustomize
        '''
        result = self._values.get("kustomize")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourcesKustomize"], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is used to refer to a source and is displayed in the UI.

        It is used in multi-source Applications.

        :schema: ApplicationOperationSyncSources#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Path is a directory path within the Git repository, and is only valid for applications sourced from Git.

        :schema: ApplicationOperationSyncSources#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def plugin(self) -> typing.Optional["ApplicationOperationSyncSourcesPlugin"]:
        '''Plugin holds config management plugin specific options.

        :schema: ApplicationOperationSyncSources#plugin
        '''
        result = self._values.get("plugin")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourcesPlugin"], result)

    @builtins.property
    def ref(self) -> typing.Optional[builtins.str]:
        '''Ref is reference to another source within sources field.

        This field will not be used if used with a ``source`` tag.

        :schema: ApplicationOperationSyncSources#ref
        '''
        result = self._values.get("ref")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_revision(self) -> typing.Optional[builtins.str]:
        '''TargetRevision defines the revision of the source to sync the application to.

        In case of Git, this can be commit, tag, or branch. If omitted, will equal to HEAD.
        In case of Helm, this is a semver tag for the Chart's version.

        :schema: ApplicationOperationSyncSources#targetRevision
        '''
        result = self._values.get("target_revision")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSources(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesDirectory",
    jsii_struct_bases=[],
    name_mapping={
        "exclude": "exclude",
        "include": "include",
        "jsonnet": "jsonnet",
        "recurse": "recurse",
    },
)
class ApplicationOperationSyncSourcesDirectory:
    def __init__(
        self,
        *,
        exclude: typing.Optional[builtins.str] = None,
        include: typing.Optional[builtins.str] = None,
        jsonnet: typing.Optional[typing.Union["ApplicationOperationSyncSourcesDirectoryJsonnet", typing.Dict[builtins.str, typing.Any]]] = None,
        recurse: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Directory holds path/directory specific options.

        :param exclude: Exclude contains a glob pattern to match paths against that should be explicitly excluded from being used during manifest generation.
        :param include: Include contains a glob pattern to match paths against that should be explicitly included during manifest generation.
        :param jsonnet: Jsonnet holds options specific to Jsonnet.
        :param recurse: Recurse specifies whether to scan a directory recursively for manifests.

        :schema: ApplicationOperationSyncSourcesDirectory
        '''
        if isinstance(jsonnet, dict):
            jsonnet = ApplicationOperationSyncSourcesDirectoryJsonnet(**jsonnet)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a46a3325ca7605bd9bd99a6a11f526fc19811dbd541f621a7808ae67cdc6ad06)
            check_type(argname="argument exclude", value=exclude, expected_type=type_hints["exclude"])
            check_type(argname="argument include", value=include, expected_type=type_hints["include"])
            check_type(argname="argument jsonnet", value=jsonnet, expected_type=type_hints["jsonnet"])
            check_type(argname="argument recurse", value=recurse, expected_type=type_hints["recurse"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if exclude is not None:
            self._values["exclude"] = exclude
        if include is not None:
            self._values["include"] = include
        if jsonnet is not None:
            self._values["jsonnet"] = jsonnet
        if recurse is not None:
            self._values["recurse"] = recurse

    @builtins.property
    def exclude(self) -> typing.Optional[builtins.str]:
        '''Exclude contains a glob pattern to match paths against that should be explicitly excluded from being used during manifest generation.

        :schema: ApplicationOperationSyncSourcesDirectory#exclude
        '''
        result = self._values.get("exclude")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def include(self) -> typing.Optional[builtins.str]:
        '''Include contains a glob pattern to match paths against that should be explicitly included during manifest generation.

        :schema: ApplicationOperationSyncSourcesDirectory#include
        '''
        result = self._values.get("include")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jsonnet(
        self,
    ) -> typing.Optional["ApplicationOperationSyncSourcesDirectoryJsonnet"]:
        '''Jsonnet holds options specific to Jsonnet.

        :schema: ApplicationOperationSyncSourcesDirectory#jsonnet
        '''
        result = self._values.get("jsonnet")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourcesDirectoryJsonnet"], result)

    @builtins.property
    def recurse(self) -> typing.Optional[builtins.bool]:
        '''Recurse specifies whether to scan a directory recursively for manifests.

        :schema: ApplicationOperationSyncSourcesDirectory#recurse
        '''
        result = self._values.get("recurse")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesDirectory(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesDirectoryJsonnet",
    jsii_struct_bases=[],
    name_mapping={"ext_vars": "extVars", "libs": "libs", "tlas": "tlas"},
)
class ApplicationOperationSyncSourcesDirectoryJsonnet:
    def __init__(
        self,
        *,
        ext_vars: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcesDirectoryJsonnetExtVars", typing.Dict[builtins.str, typing.Any]]]] = None,
        libs: typing.Optional[typing.Sequence[builtins.str]] = None,
        tlas: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcesDirectoryJsonnetTlas", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Jsonnet holds options specific to Jsonnet.

        :param ext_vars: ExtVars is a list of Jsonnet External Variables.
        :param libs: Additional library search dirs.
        :param tlas: TLAS is a list of Jsonnet Top-level Arguments.

        :schema: ApplicationOperationSyncSourcesDirectoryJsonnet
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__87d35197c04ba87c1a789fa31c8888a79d40cc1f7cb28ab4376ac20fa408da4e)
            check_type(argname="argument ext_vars", value=ext_vars, expected_type=type_hints["ext_vars"])
            check_type(argname="argument libs", value=libs, expected_type=type_hints["libs"])
            check_type(argname="argument tlas", value=tlas, expected_type=type_hints["tlas"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if ext_vars is not None:
            self._values["ext_vars"] = ext_vars
        if libs is not None:
            self._values["libs"] = libs
        if tlas is not None:
            self._values["tlas"] = tlas

    @builtins.property
    def ext_vars(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcesDirectoryJsonnetExtVars"]]:
        '''ExtVars is a list of Jsonnet External Variables.

        :schema: ApplicationOperationSyncSourcesDirectoryJsonnet#extVars
        '''
        result = self._values.get("ext_vars")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcesDirectoryJsonnetExtVars"]], result)

    @builtins.property
    def libs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Additional library search dirs.

        :schema: ApplicationOperationSyncSourcesDirectoryJsonnet#libs
        '''
        result = self._values.get("libs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def tlas(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcesDirectoryJsonnetTlas"]]:
        '''TLAS is a list of Jsonnet Top-level Arguments.

        :schema: ApplicationOperationSyncSourcesDirectoryJsonnet#tlas
        '''
        result = self._values.get("tlas")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcesDirectoryJsonnetTlas"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesDirectoryJsonnet(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesDirectoryJsonnetExtVars",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value", "code": "code"},
)
class ApplicationOperationSyncSourcesDirectoryJsonnetExtVars:
    def __init__(
        self,
        *,
        name: builtins.str,
        value: builtins.str,
        code: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''JsonnetVar represents a variable to be passed to jsonnet during manifest generation.

        :param name: 
        :param value: 
        :param code: 

        :schema: ApplicationOperationSyncSourcesDirectoryJsonnetExtVars
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f845fe54066037fc6f242f792fba6bf3dd774271a8b0016ead34aa68b9495502)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument code", value=code, expected_type=type_hints["code"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }
        if code is not None:
            self._values["code"] = code

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncSourcesDirectoryJsonnetExtVars#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncSourcesDirectoryJsonnetExtVars#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def code(self) -> typing.Optional[builtins.bool]:
        '''
        :schema: ApplicationOperationSyncSourcesDirectoryJsonnetExtVars#code
        '''
        result = self._values.get("code")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesDirectoryJsonnetExtVars(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesDirectoryJsonnetTlas",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value", "code": "code"},
)
class ApplicationOperationSyncSourcesDirectoryJsonnetTlas:
    def __init__(
        self,
        *,
        name: builtins.str,
        value: builtins.str,
        code: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''JsonnetVar represents a variable to be passed to jsonnet during manifest generation.

        :param name: 
        :param value: 
        :param code: 

        :schema: ApplicationOperationSyncSourcesDirectoryJsonnetTlas
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__119ae484e7760b7c5e5c31d6da4e48022a181b8a8349c4b575999fd8dcffefd9)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument code", value=code, expected_type=type_hints["code"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }
        if code is not None:
            self._values["code"] = code

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncSourcesDirectoryJsonnetTlas#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationOperationSyncSourcesDirectoryJsonnetTlas#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def code(self) -> typing.Optional[builtins.bool]:
        '''
        :schema: ApplicationOperationSyncSourcesDirectoryJsonnetTlas#code
        '''
        result = self._values.get("code")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesDirectoryJsonnetTlas(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesHelm",
    jsii_struct_bases=[],
    name_mapping={
        "api_versions": "apiVersions",
        "file_parameters": "fileParameters",
        "ignore_missing_value_files": "ignoreMissingValueFiles",
        "kube_version": "kubeVersion",
        "namespace": "namespace",
        "parameters": "parameters",
        "pass_credentials": "passCredentials",
        "release_name": "releaseName",
        "skip_crds": "skipCrds",
        "skip_schema_validation": "skipSchemaValidation",
        "skip_tests": "skipTests",
        "value_files": "valueFiles",
        "values": "values",
        "values_object": "valuesObject",
        "version": "version",
    },
)
class ApplicationOperationSyncSourcesHelm:
    def __init__(
        self,
        *,
        api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
        file_parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcesHelmFileParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_missing_value_files: typing.Optional[builtins.bool] = None,
        kube_version: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcesHelmParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
        pass_credentials: typing.Optional[builtins.bool] = None,
        release_name: typing.Optional[builtins.str] = None,
        skip_crds: typing.Optional[builtins.bool] = None,
        skip_schema_validation: typing.Optional[builtins.bool] = None,
        skip_tests: typing.Optional[builtins.bool] = None,
        value_files: typing.Optional[typing.Sequence[builtins.str]] = None,
        values: typing.Optional[builtins.str] = None,
        values_object: typing.Any = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Helm holds helm specific options.

        :param api_versions: APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests. By default, Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.
        :param file_parameters: FileParameters are file parameters to the helm template.
        :param ignore_missing_value_files: IgnoreMissingValueFiles prevents helm template from failing when valueFiles do not exist locally by not appending them to helm template --values.
        :param kube_version: KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests. By default, Argo CD uses the Kubernetes version of the target cluster.
        :param namespace: Namespace is an optional namespace to template with. If left empty, defaults to the app's destination namespace.
        :param parameters: Parameters is a list of Helm parameters which are passed to the helm template command upon manifest generation.
        :param pass_credentials: PassCredentials pass credentials to all domains (Helm's --pass-credentials).
        :param release_name: ReleaseName is the Helm release name to use. If omitted it will use the application name
        :param skip_crds: SkipCrds skips custom resource definition installation step (Helm's --skip-crds).
        :param skip_schema_validation: SkipSchemaValidation skips JSON schema validation (Helm's --skip-schema-validation).
        :param skip_tests: SkipTests skips test manifest installation step (Helm's --skip-tests).
        :param value_files: ValuesFiles is a list of Helm value files to use when generating a template.
        :param values: Values specifies Helm values to be passed to helm template, typically defined as a block. ValuesObject takes precedence over Values, so use one or the other.
        :param values_object: ValuesObject specifies Helm values to be passed to helm template, defined as a map. This takes precedence over Values.
        :param version: Version is the Helm version to use for templating ("3").

        :schema: ApplicationOperationSyncSourcesHelm
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__172ec38f042e07af6143f0fbd294bba3113923d59563a3a268a2bd4efe74d50d)
            check_type(argname="argument api_versions", value=api_versions, expected_type=type_hints["api_versions"])
            check_type(argname="argument file_parameters", value=file_parameters, expected_type=type_hints["file_parameters"])
            check_type(argname="argument ignore_missing_value_files", value=ignore_missing_value_files, expected_type=type_hints["ignore_missing_value_files"])
            check_type(argname="argument kube_version", value=kube_version, expected_type=type_hints["kube_version"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
            check_type(argname="argument pass_credentials", value=pass_credentials, expected_type=type_hints["pass_credentials"])
            check_type(argname="argument release_name", value=release_name, expected_type=type_hints["release_name"])
            check_type(argname="argument skip_crds", value=skip_crds, expected_type=type_hints["skip_crds"])
            check_type(argname="argument skip_schema_validation", value=skip_schema_validation, expected_type=type_hints["skip_schema_validation"])
            check_type(argname="argument skip_tests", value=skip_tests, expected_type=type_hints["skip_tests"])
            check_type(argname="argument value_files", value=value_files, expected_type=type_hints["value_files"])
            check_type(argname="argument values", value=values, expected_type=type_hints["values"])
            check_type(argname="argument values_object", value=values_object, expected_type=type_hints["values_object"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_versions is not None:
            self._values["api_versions"] = api_versions
        if file_parameters is not None:
            self._values["file_parameters"] = file_parameters
        if ignore_missing_value_files is not None:
            self._values["ignore_missing_value_files"] = ignore_missing_value_files
        if kube_version is not None:
            self._values["kube_version"] = kube_version
        if namespace is not None:
            self._values["namespace"] = namespace
        if parameters is not None:
            self._values["parameters"] = parameters
        if pass_credentials is not None:
            self._values["pass_credentials"] = pass_credentials
        if release_name is not None:
            self._values["release_name"] = release_name
        if skip_crds is not None:
            self._values["skip_crds"] = skip_crds
        if skip_schema_validation is not None:
            self._values["skip_schema_validation"] = skip_schema_validation
        if skip_tests is not None:
            self._values["skip_tests"] = skip_tests
        if value_files is not None:
            self._values["value_files"] = value_files
        if values is not None:
            self._values["values"] = values
        if values_object is not None:
            self._values["values_object"] = values_object
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def api_versions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests.

        By default,
        Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.

        :schema: ApplicationOperationSyncSourcesHelm#apiVersions
        '''
        result = self._values.get("api_versions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def file_parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcesHelmFileParameters"]]:
        '''FileParameters are file parameters to the helm template.

        :schema: ApplicationOperationSyncSourcesHelm#fileParameters
        '''
        result = self._values.get("file_parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcesHelmFileParameters"]], result)

    @builtins.property
    def ignore_missing_value_files(self) -> typing.Optional[builtins.bool]:
        '''IgnoreMissingValueFiles prevents helm template from failing when valueFiles do not exist locally by not appending them to helm template --values.

        :schema: ApplicationOperationSyncSourcesHelm#ignoreMissingValueFiles
        '''
        result = self._values.get("ignore_missing_value_files")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def kube_version(self) -> typing.Optional[builtins.str]:
        '''KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests.

        By default, Argo CD
        uses the Kubernetes version of the target cluster.

        :schema: ApplicationOperationSyncSourcesHelm#kubeVersion
        '''
        result = self._values.get("kube_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace is an optional namespace to template with.

        If left empty, defaults to the app's destination namespace.

        :schema: ApplicationOperationSyncSourcesHelm#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcesHelmParameters"]]:
        '''Parameters is a list of Helm parameters which are passed to the helm template command upon manifest generation.

        :schema: ApplicationOperationSyncSourcesHelm#parameters
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcesHelmParameters"]], result)

    @builtins.property
    def pass_credentials(self) -> typing.Optional[builtins.bool]:
        '''PassCredentials pass credentials to all domains (Helm's --pass-credentials).

        :schema: ApplicationOperationSyncSourcesHelm#passCredentials
        '''
        result = self._values.get("pass_credentials")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_name(self) -> typing.Optional[builtins.str]:
        '''ReleaseName is the Helm release name to use.

        If omitted it will use the application name

        :schema: ApplicationOperationSyncSourcesHelm#releaseName
        '''
        result = self._values.get("release_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def skip_crds(self) -> typing.Optional[builtins.bool]:
        '''SkipCrds skips custom resource definition installation step (Helm's --skip-crds).

        :schema: ApplicationOperationSyncSourcesHelm#skipCrds
        '''
        result = self._values.get("skip_crds")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip_schema_validation(self) -> typing.Optional[builtins.bool]:
        '''SkipSchemaValidation skips JSON schema validation (Helm's --skip-schema-validation).

        :schema: ApplicationOperationSyncSourcesHelm#skipSchemaValidation
        '''
        result = self._values.get("skip_schema_validation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip_tests(self) -> typing.Optional[builtins.bool]:
        '''SkipTests skips test manifest installation step (Helm's --skip-tests).

        :schema: ApplicationOperationSyncSourcesHelm#skipTests
        '''
        result = self._values.get("skip_tests")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def value_files(self) -> typing.Optional[typing.List[builtins.str]]:
        '''ValuesFiles is a list of Helm value files to use when generating a template.

        :schema: ApplicationOperationSyncSourcesHelm#valueFiles
        '''
        result = self._values.get("value_files")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def values(self) -> typing.Optional[builtins.str]:
        '''Values specifies Helm values to be passed to helm template, typically defined as a block.

        ValuesObject takes precedence over Values, so use one or the other.

        :schema: ApplicationOperationSyncSourcesHelm#values
        '''
        result = self._values.get("values")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def values_object(self) -> typing.Any:
        '''ValuesObject specifies Helm values to be passed to helm template, defined as a map.

        This takes precedence over Values.

        :schema: ApplicationOperationSyncSourcesHelm#valuesObject
        '''
        result = self._values.get("values_object")
        return typing.cast(typing.Any, result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version is the Helm version to use for templating ("3").

        :schema: ApplicationOperationSyncSourcesHelm#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesHelm(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesHelmFileParameters",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "path": "path"},
)
class ApplicationOperationSyncSourcesHelmFileParameters:
    def __init__(
        self,
        *,
        name: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HelmFileParameter is a file parameter that's passed to helm template during manifest generation.

        :param name: Name is the name of the Helm parameter.
        :param path: Path is the path to the file containing the values for the Helm parameter.

        :schema: ApplicationOperationSyncSourcesHelmFileParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__deb5d515c7d023132be81c0369a565e64264d605fa91e5fbed6f7f94ba0170ad)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if name is not None:
            self._values["name"] = name
        if path is not None:
            self._values["path"] = path

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name of the Helm parameter.

        :schema: ApplicationOperationSyncSourcesHelmFileParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Path is the path to the file containing the values for the Helm parameter.

        :schema: ApplicationOperationSyncSourcesHelmFileParameters#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesHelmFileParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesHelmParameters",
    jsii_struct_bases=[],
    name_mapping={"force_string": "forceString", "name": "name", "value": "value"},
)
class ApplicationOperationSyncSourcesHelmParameters:
    def __init__(
        self,
        *,
        force_string: typing.Optional[builtins.bool] = None,
        name: typing.Optional[builtins.str] = None,
        value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HelmParameter is a parameter that's passed to helm template during manifest generation.

        :param force_string: ForceString determines whether to tell Helm to interpret booleans and numbers as strings.
        :param name: Name is the name of the Helm parameter.
        :param value: Value is the value for the Helm parameter.

        :schema: ApplicationOperationSyncSourcesHelmParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__39bf4f2b544187283cac9d2abd9e46d60c344009202a4ac76c70bbc6c4cce358)
            check_type(argname="argument force_string", value=force_string, expected_type=type_hints["force_string"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if force_string is not None:
            self._values["force_string"] = force_string
        if name is not None:
            self._values["name"] = name
        if value is not None:
            self._values["value"] = value

    @builtins.property
    def force_string(self) -> typing.Optional[builtins.bool]:
        '''ForceString determines whether to tell Helm to interpret booleans and numbers as strings.

        :schema: ApplicationOperationSyncSourcesHelmParameters#forceString
        '''
        result = self._values.get("force_string")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name of the Helm parameter.

        :schema: ApplicationOperationSyncSourcesHelmParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def value(self) -> typing.Optional[builtins.str]:
        '''Value is the value for the Helm parameter.

        :schema: ApplicationOperationSyncSourcesHelmParameters#value
        '''
        result = self._values.get("value")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesHelmParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesKustomize",
    jsii_struct_bases=[],
    name_mapping={
        "api_versions": "apiVersions",
        "common_annotations": "commonAnnotations",
        "common_annotations_envsubst": "commonAnnotationsEnvsubst",
        "common_labels": "commonLabels",
        "components": "components",
        "force_common_annotations": "forceCommonAnnotations",
        "force_common_labels": "forceCommonLabels",
        "ignore_missing_components": "ignoreMissingComponents",
        "images": "images",
        "kube_version": "kubeVersion",
        "label_include_templates": "labelIncludeTemplates",
        "label_without_selector": "labelWithoutSelector",
        "name_prefix": "namePrefix",
        "namespace": "namespace",
        "name_suffix": "nameSuffix",
        "patches": "patches",
        "replicas": "replicas",
        "version": "version",
    },
)
class ApplicationOperationSyncSourcesKustomize:
    def __init__(
        self,
        *,
        api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
        common_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        common_annotations_envsubst: typing.Optional[builtins.bool] = None,
        common_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        components: typing.Optional[typing.Sequence[builtins.str]] = None,
        force_common_annotations: typing.Optional[builtins.bool] = None,
        force_common_labels: typing.Optional[builtins.bool] = None,
        ignore_missing_components: typing.Optional[builtins.bool] = None,
        images: typing.Optional[typing.Sequence[builtins.str]] = None,
        kube_version: typing.Optional[builtins.str] = None,
        label_include_templates: typing.Optional[builtins.bool] = None,
        label_without_selector: typing.Optional[builtins.bool] = None,
        name_prefix: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        name_suffix: typing.Optional[builtins.str] = None,
        patches: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcesKustomizePatches", typing.Dict[builtins.str, typing.Any]]]] = None,
        replicas: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcesKustomizeReplicas", typing.Dict[builtins.str, typing.Any]]]] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Kustomize holds kustomize specific options.

        :param api_versions: APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests. By default, Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.
        :param common_annotations: CommonAnnotations is a list of additional annotations to add to rendered manifests.
        :param common_annotations_envsubst: CommonAnnotationsEnvsubst specifies whether to apply env variables substitution for annotation values.
        :param common_labels: CommonLabels is a list of additional labels to add to rendered manifests.
        :param components: Components specifies a list of kustomize components to add to the kustomization before building.
        :param force_common_annotations: ForceCommonAnnotations specifies whether to force applying common annotations to resources for Kustomize apps.
        :param force_common_labels: ForceCommonLabels specifies whether to force applying common labels to resources for Kustomize apps.
        :param ignore_missing_components: IgnoreMissingComponents prevents kustomize from failing when components do not exist locally by not appending them to kustomization file.
        :param images: Images is a list of Kustomize image override specifications.
        :param kube_version: KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests. By default, Argo CD uses the Kubernetes version of the target cluster.
        :param label_include_templates: LabelIncludeTemplates specifies whether to apply common labels to resource templates or not.
        :param label_without_selector: LabelWithoutSelector specifies whether to apply common labels to resource selectors or not.
        :param name_prefix: NamePrefix is a prefix appended to resources for Kustomize apps.
        :param namespace: Namespace sets the namespace that Kustomize adds to all resources.
        :param name_suffix: NameSuffix is a suffix appended to resources for Kustomize apps.
        :param patches: Patches is a list of Kustomize patches.
        :param replicas: Replicas is a list of Kustomize Replicas override specifications.
        :param version: Version controls which version of Kustomize to use for rendering manifests.

        :schema: ApplicationOperationSyncSourcesKustomize
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__79be8f5bac148dd707962053a8ca1de26f8110b882327403e40e1b6d86abe2e7)
            check_type(argname="argument api_versions", value=api_versions, expected_type=type_hints["api_versions"])
            check_type(argname="argument common_annotations", value=common_annotations, expected_type=type_hints["common_annotations"])
            check_type(argname="argument common_annotations_envsubst", value=common_annotations_envsubst, expected_type=type_hints["common_annotations_envsubst"])
            check_type(argname="argument common_labels", value=common_labels, expected_type=type_hints["common_labels"])
            check_type(argname="argument components", value=components, expected_type=type_hints["components"])
            check_type(argname="argument force_common_annotations", value=force_common_annotations, expected_type=type_hints["force_common_annotations"])
            check_type(argname="argument force_common_labels", value=force_common_labels, expected_type=type_hints["force_common_labels"])
            check_type(argname="argument ignore_missing_components", value=ignore_missing_components, expected_type=type_hints["ignore_missing_components"])
            check_type(argname="argument images", value=images, expected_type=type_hints["images"])
            check_type(argname="argument kube_version", value=kube_version, expected_type=type_hints["kube_version"])
            check_type(argname="argument label_include_templates", value=label_include_templates, expected_type=type_hints["label_include_templates"])
            check_type(argname="argument label_without_selector", value=label_without_selector, expected_type=type_hints["label_without_selector"])
            check_type(argname="argument name_prefix", value=name_prefix, expected_type=type_hints["name_prefix"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument name_suffix", value=name_suffix, expected_type=type_hints["name_suffix"])
            check_type(argname="argument patches", value=patches, expected_type=type_hints["patches"])
            check_type(argname="argument replicas", value=replicas, expected_type=type_hints["replicas"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_versions is not None:
            self._values["api_versions"] = api_versions
        if common_annotations is not None:
            self._values["common_annotations"] = common_annotations
        if common_annotations_envsubst is not None:
            self._values["common_annotations_envsubst"] = common_annotations_envsubst
        if common_labels is not None:
            self._values["common_labels"] = common_labels
        if components is not None:
            self._values["components"] = components
        if force_common_annotations is not None:
            self._values["force_common_annotations"] = force_common_annotations
        if force_common_labels is not None:
            self._values["force_common_labels"] = force_common_labels
        if ignore_missing_components is not None:
            self._values["ignore_missing_components"] = ignore_missing_components
        if images is not None:
            self._values["images"] = images
        if kube_version is not None:
            self._values["kube_version"] = kube_version
        if label_include_templates is not None:
            self._values["label_include_templates"] = label_include_templates
        if label_without_selector is not None:
            self._values["label_without_selector"] = label_without_selector
        if name_prefix is not None:
            self._values["name_prefix"] = name_prefix
        if namespace is not None:
            self._values["namespace"] = namespace
        if name_suffix is not None:
            self._values["name_suffix"] = name_suffix
        if patches is not None:
            self._values["patches"] = patches
        if replicas is not None:
            self._values["replicas"] = replicas
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def api_versions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests.

        By default,
        Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.

        :schema: ApplicationOperationSyncSourcesKustomize#apiVersions
        '''
        result = self._values.get("api_versions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def common_annotations(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''CommonAnnotations is a list of additional annotations to add to rendered manifests.

        :schema: ApplicationOperationSyncSourcesKustomize#commonAnnotations
        '''
        result = self._values.get("common_annotations")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def common_annotations_envsubst(self) -> typing.Optional[builtins.bool]:
        '''CommonAnnotationsEnvsubst specifies whether to apply env variables substitution for annotation values.

        :schema: ApplicationOperationSyncSourcesKustomize#commonAnnotationsEnvsubst
        '''
        result = self._values.get("common_annotations_envsubst")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def common_labels(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''CommonLabels is a list of additional labels to add to rendered manifests.

        :schema: ApplicationOperationSyncSourcesKustomize#commonLabels
        '''
        result = self._values.get("common_labels")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def components(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Components specifies a list of kustomize components to add to the kustomization before building.

        :schema: ApplicationOperationSyncSourcesKustomize#components
        '''
        result = self._values.get("components")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def force_common_annotations(self) -> typing.Optional[builtins.bool]:
        '''ForceCommonAnnotations specifies whether to force applying common annotations to resources for Kustomize apps.

        :schema: ApplicationOperationSyncSourcesKustomize#forceCommonAnnotations
        '''
        result = self._values.get("force_common_annotations")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def force_common_labels(self) -> typing.Optional[builtins.bool]:
        '''ForceCommonLabels specifies whether to force applying common labels to resources for Kustomize apps.

        :schema: ApplicationOperationSyncSourcesKustomize#forceCommonLabels
        '''
        result = self._values.get("force_common_labels")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def ignore_missing_components(self) -> typing.Optional[builtins.bool]:
        '''IgnoreMissingComponents prevents kustomize from failing when components do not exist locally by not appending them to kustomization file.

        :schema: ApplicationOperationSyncSourcesKustomize#ignoreMissingComponents
        '''
        result = self._values.get("ignore_missing_components")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def images(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Images is a list of Kustomize image override specifications.

        :schema: ApplicationOperationSyncSourcesKustomize#images
        '''
        result = self._values.get("images")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def kube_version(self) -> typing.Optional[builtins.str]:
        '''KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests.

        By default, Argo CD
        uses the Kubernetes version of the target cluster.

        :schema: ApplicationOperationSyncSourcesKustomize#kubeVersion
        '''
        result = self._values.get("kube_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def label_include_templates(self) -> typing.Optional[builtins.bool]:
        '''LabelIncludeTemplates specifies whether to apply common labels to resource templates or not.

        :schema: ApplicationOperationSyncSourcesKustomize#labelIncludeTemplates
        '''
        result = self._values.get("label_include_templates")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def label_without_selector(self) -> typing.Optional[builtins.bool]:
        '''LabelWithoutSelector specifies whether to apply common labels to resource selectors or not.

        :schema: ApplicationOperationSyncSourcesKustomize#labelWithoutSelector
        '''
        result = self._values.get("label_without_selector")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def name_prefix(self) -> typing.Optional[builtins.str]:
        '''NamePrefix is a prefix appended to resources for Kustomize apps.

        :schema: ApplicationOperationSyncSourcesKustomize#namePrefix
        '''
        result = self._values.get("name_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace sets the namespace that Kustomize adds to all resources.

        :schema: ApplicationOperationSyncSourcesKustomize#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name_suffix(self) -> typing.Optional[builtins.str]:
        '''NameSuffix is a suffix appended to resources for Kustomize apps.

        :schema: ApplicationOperationSyncSourcesKustomize#nameSuffix
        '''
        result = self._values.get("name_suffix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def patches(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcesKustomizePatches"]]:
        '''Patches is a list of Kustomize patches.

        :schema: ApplicationOperationSyncSourcesKustomize#patches
        '''
        result = self._values.get("patches")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcesKustomizePatches"]], result)

    @builtins.property
    def replicas(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcesKustomizeReplicas"]]:
        '''Replicas is a list of Kustomize Replicas override specifications.

        :schema: ApplicationOperationSyncSourcesKustomize#replicas
        '''
        result = self._values.get("replicas")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcesKustomizeReplicas"]], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version controls which version of Kustomize to use for rendering manifests.

        :schema: ApplicationOperationSyncSourcesKustomize#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesKustomize(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesKustomizePatches",
    jsii_struct_bases=[],
    name_mapping={
        "options": "options",
        "patch": "patch",
        "path": "path",
        "target": "target",
    },
)
class ApplicationOperationSyncSourcesKustomizePatches:
    def __init__(
        self,
        *,
        options: typing.Optional[typing.Mapping[builtins.str, builtins.bool]] = None,
        patch: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        target: typing.Optional[typing.Union["ApplicationOperationSyncSourcesKustomizePatchesTarget", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param options: 
        :param patch: 
        :param path: 
        :param target: 

        :schema: ApplicationOperationSyncSourcesKustomizePatches
        '''
        if isinstance(target, dict):
            target = ApplicationOperationSyncSourcesKustomizePatchesTarget(**target)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__35d939365f71fe69445ede174ee8ec31bc6cc3e80247f046e0224c51a5462014)
            check_type(argname="argument options", value=options, expected_type=type_hints["options"])
            check_type(argname="argument patch", value=patch, expected_type=type_hints["patch"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if options is not None:
            self._values["options"] = options
        if patch is not None:
            self._values["patch"] = patch
        if path is not None:
            self._values["path"] = path
        if target is not None:
            self._values["target"] = target

    @builtins.property
    def options(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.bool]]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatches#options
        '''
        result = self._values.get("options")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.bool]], result)

    @builtins.property
    def patch(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatches#patch
        '''
        result = self._values.get("patch")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatches#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target(
        self,
    ) -> typing.Optional["ApplicationOperationSyncSourcesKustomizePatchesTarget"]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatches#target
        '''
        result = self._values.get("target")
        return typing.cast(typing.Optional["ApplicationOperationSyncSourcesKustomizePatchesTarget"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesKustomizePatches(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesKustomizePatchesTarget",
    jsii_struct_bases=[],
    name_mapping={
        "annotation_selector": "annotationSelector",
        "group": "group",
        "kind": "kind",
        "label_selector": "labelSelector",
        "name": "name",
        "namespace": "namespace",
        "version": "version",
    },
)
class ApplicationOperationSyncSourcesKustomizePatchesTarget:
    def __init__(
        self,
        *,
        annotation_selector: typing.Optional[builtins.str] = None,
        group: typing.Optional[builtins.str] = None,
        kind: typing.Optional[builtins.str] = None,
        label_selector: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param annotation_selector: 
        :param group: 
        :param kind: 
        :param label_selector: 
        :param name: 
        :param namespace: 
        :param version: 

        :schema: ApplicationOperationSyncSourcesKustomizePatchesTarget
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__83a5f7991cb91a81bade59aca319c06a7a8d514661075fb6cf2d5b9a87b695d3)
            check_type(argname="argument annotation_selector", value=annotation_selector, expected_type=type_hints["annotation_selector"])
            check_type(argname="argument group", value=group, expected_type=type_hints["group"])
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument label_selector", value=label_selector, expected_type=type_hints["label_selector"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if annotation_selector is not None:
            self._values["annotation_selector"] = annotation_selector
        if group is not None:
            self._values["group"] = group
        if kind is not None:
            self._values["kind"] = kind
        if label_selector is not None:
            self._values["label_selector"] = label_selector
        if name is not None:
            self._values["name"] = name
        if namespace is not None:
            self._values["namespace"] = namespace
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def annotation_selector(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatchesTarget#annotationSelector
        '''
        result = self._values.get("annotation_selector")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def group(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatchesTarget#group
        '''
        result = self._values.get("group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def kind(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatchesTarget#kind
        '''
        result = self._values.get("kind")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def label_selector(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatchesTarget#labelSelector
        '''
        result = self._values.get("label_selector")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatchesTarget#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatchesTarget#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesKustomizePatchesTarget#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesKustomizePatchesTarget(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesKustomizeReplicas",
    jsii_struct_bases=[],
    name_mapping={"count": "count", "name": "name"},
)
class ApplicationOperationSyncSourcesKustomizeReplicas:
    def __init__(
        self,
        *,
        count: "ApplicationOperationSyncSourcesKustomizeReplicasCount",
        name: builtins.str,
    ) -> None:
        '''
        :param count: Number of replicas.
        :param name: Name of Deployment or StatefulSet.

        :schema: ApplicationOperationSyncSourcesKustomizeReplicas
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e90621a15a04d2a0abf5ad20f8a2278f407c66feb183be6418300bd5505a54c1)
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "count": count,
            "name": name,
        }

    @builtins.property
    def count(self) -> "ApplicationOperationSyncSourcesKustomizeReplicasCount":
        '''Number of replicas.

        :schema: ApplicationOperationSyncSourcesKustomizeReplicas#count
        '''
        result = self._values.get("count")
        assert result is not None, "Required property 'count' is missing"
        return typing.cast("ApplicationOperationSyncSourcesKustomizeReplicasCount", result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of Deployment or StatefulSet.

        :schema: ApplicationOperationSyncSourcesKustomizeReplicas#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesKustomizeReplicas(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ApplicationOperationSyncSourcesKustomizeReplicasCount(
    metaclass=jsii.JSIIMeta,
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesKustomizeReplicasCount",
):
    '''Number of replicas.

    :schema: ApplicationOperationSyncSourcesKustomizeReplicasCount
    '''

    @jsii.member(jsii_name="fromNumber")
    @builtins.classmethod
    def from_number(
        cls,
        value: jsii.Number,
    ) -> "ApplicationOperationSyncSourcesKustomizeReplicasCount":
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40bc0586fcf2db62ae35e6b94c7a27ad159b312b7d1884ce1c1e01a7eee59271)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast("ApplicationOperationSyncSourcesKustomizeReplicasCount", jsii.sinvoke(cls, "fromNumber", [value]))

    @jsii.member(jsii_name="fromString")
    @builtins.classmethod
    def from_string(
        cls,
        value: builtins.str,
    ) -> "ApplicationOperationSyncSourcesKustomizeReplicasCount":
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__833a26a87ec1d217269e4e8f93f71e9ab97901518350c8420bf4fb6208c411dc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast("ApplicationOperationSyncSourcesKustomizeReplicasCount", jsii.sinvoke(cls, "fromString", [value]))

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(self) -> typing.Union[builtins.str, jsii.Number]:
        return typing.cast(typing.Union[builtins.str, jsii.Number], jsii.get(self, "value"))


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesPlugin",
    jsii_struct_bases=[],
    name_mapping={"env": "env", "name": "name", "parameters": "parameters"},
)
class ApplicationOperationSyncSourcesPlugin:
    def __init__(
        self,
        *,
        env: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcesPluginEnv", typing.Dict[builtins.str, typing.Any]]]] = None,
        name: typing.Optional[builtins.str] = None,
        parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationOperationSyncSourcesPluginParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Plugin holds config management plugin specific options.

        :param env: Env is a list of environment variable entries.
        :param name: 
        :param parameters: 

        :schema: ApplicationOperationSyncSourcesPlugin
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__21184de0aef8faddfe3a2c91cea28a1d6c60985733e822046dfc080e4d1e777f)
            check_type(argname="argument env", value=env, expected_type=type_hints["env"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if env is not None:
            self._values["env"] = env
        if name is not None:
            self._values["name"] = name
        if parameters is not None:
            self._values["parameters"] = parameters

    @builtins.property
    def env(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcesPluginEnv"]]:
        '''Env is a list of environment variable entries.

        :schema: ApplicationOperationSyncSourcesPlugin#env
        '''
        result = self._values.get("env")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcesPluginEnv"]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationOperationSyncSourcesPlugin#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationOperationSyncSourcesPluginParameters"]]:
        '''
        :schema: ApplicationOperationSyncSourcesPlugin#parameters
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationOperationSyncSourcesPluginParameters"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesPlugin(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesPluginEnv",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value"},
)
class ApplicationOperationSyncSourcesPluginEnv:
    def __init__(self, *, name: builtins.str, value: builtins.str) -> None:
        '''EnvEntry represents an entry in the application's environment.

        :param name: Name is the name of the variable, usually expressed in uppercase.
        :param value: Value is the value of the variable.

        :schema: ApplicationOperationSyncSourcesPluginEnv
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2b4d2c4cecda1d8199b9061516e8bd0af91b9461eb3ebb25f303e38603445162)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''Name is the name of the variable, usually expressed in uppercase.

        :schema: ApplicationOperationSyncSourcesPluginEnv#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''Value is the value of the variable.

        :schema: ApplicationOperationSyncSourcesPluginEnv#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesPluginEnv(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSourcesPluginParameters",
    jsii_struct_bases=[],
    name_mapping={"array": "array", "map": "map", "name": "name", "string": "string"},
)
class ApplicationOperationSyncSourcesPluginParameters:
    def __init__(
        self,
        *,
        array: typing.Optional[typing.Sequence[builtins.str]] = None,
        map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        string: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param array: Array is the value of an array type parameter.
        :param map: Map is the value of a map type parameter.
        :param name: Name is the name identifying a parameter.
        :param string: String_ is the value of a string type parameter.

        :schema: ApplicationOperationSyncSourcesPluginParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b31e1c1123fd42d5ebe1ee1cc773723f111f370a9979ada34364ead2f6781366)
            check_type(argname="argument array", value=array, expected_type=type_hints["array"])
            check_type(argname="argument map", value=map, expected_type=type_hints["map"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument string", value=string, expected_type=type_hints["string"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if array is not None:
            self._values["array"] = array
        if map is not None:
            self._values["map"] = map
        if name is not None:
            self._values["name"] = name
        if string is not None:
            self._values["string"] = string

    @builtins.property
    def array(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array is the value of an array type parameter.

        :schema: ApplicationOperationSyncSourcesPluginParameters#array
        '''
        result = self._values.get("array")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def map(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Map is the value of a map type parameter.

        :schema: ApplicationOperationSyncSourcesPluginParameters#map
        '''
        result = self._values.get("map")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name identifying a parameter.

        :schema: ApplicationOperationSyncSourcesPluginParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def string(self) -> typing.Optional[builtins.str]:
        '''String_ is the value of a string type parameter.

        :schema: ApplicationOperationSyncSourcesPluginParameters#string
        '''
        result = self._values.get("string")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSourcesPluginParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSyncStrategy",
    jsii_struct_bases=[],
    name_mapping={"apply": "apply", "hook": "hook"},
)
class ApplicationOperationSyncSyncStrategy:
    def __init__(
        self,
        *,
        apply: typing.Optional[typing.Union["ApplicationOperationSyncSyncStrategyApply", typing.Dict[builtins.str, typing.Any]]] = None,
        hook: typing.Optional[typing.Union["ApplicationOperationSyncSyncStrategyHook", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''SyncStrategy describes how to perform the sync.

        :param apply: Apply will perform a ``kubectl apply`` to perform the sync.
        :param hook: Hook will submit any referenced resources to perform the sync. This is the default strategy

        :schema: ApplicationOperationSyncSyncStrategy
        '''
        if isinstance(apply, dict):
            apply = ApplicationOperationSyncSyncStrategyApply(**apply)
        if isinstance(hook, dict):
            hook = ApplicationOperationSyncSyncStrategyHook(**hook)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eeac69098ed9b189e55486c4c824870596c6d1bfa56e5ac75b42a9922a978241)
            check_type(argname="argument apply", value=apply, expected_type=type_hints["apply"])
            check_type(argname="argument hook", value=hook, expected_type=type_hints["hook"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if apply is not None:
            self._values["apply"] = apply
        if hook is not None:
            self._values["hook"] = hook

    @builtins.property
    def apply(self) -> typing.Optional["ApplicationOperationSyncSyncStrategyApply"]:
        '''Apply will perform a ``kubectl apply`` to perform the sync.

        :schema: ApplicationOperationSyncSyncStrategy#apply
        '''
        result = self._values.get("apply")
        return typing.cast(typing.Optional["ApplicationOperationSyncSyncStrategyApply"], result)

    @builtins.property
    def hook(self) -> typing.Optional["ApplicationOperationSyncSyncStrategyHook"]:
        '''Hook will submit any referenced resources to perform the sync.

        This is the default strategy

        :schema: ApplicationOperationSyncSyncStrategy#hook
        '''
        result = self._values.get("hook")
        return typing.cast(typing.Optional["ApplicationOperationSyncSyncStrategyHook"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSyncStrategy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSyncStrategyApply",
    jsii_struct_bases=[],
    name_mapping={"force": "force"},
)
class ApplicationOperationSyncSyncStrategyApply:
    def __init__(self, *, force: typing.Optional[builtins.bool] = None) -> None:
        '''Apply will perform a ``kubectl apply`` to perform the sync.

        :param force: Force indicates whether or not to supply the --force flag to ``kubectl apply``. The --force flag deletes and re-create the resource, when PATCH encounters conflict and has retried for 5 times.

        :schema: ApplicationOperationSyncSyncStrategyApply
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5dffa8693690076d84c566d163f7109d618d9bc491d9af0acaade089d1893aef)
            check_type(argname="argument force", value=force, expected_type=type_hints["force"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if force is not None:
            self._values["force"] = force

    @builtins.property
    def force(self) -> typing.Optional[builtins.bool]:
        '''Force indicates whether or not to supply the --force flag to ``kubectl apply``.

        The --force flag deletes and re-create the resource, when PATCH encounters conflict and has
        retried for 5 times.

        :schema: ApplicationOperationSyncSyncStrategyApply#force
        '''
        result = self._values.get("force")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSyncStrategyApply(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationOperationSyncSyncStrategyHook",
    jsii_struct_bases=[],
    name_mapping={"force": "force"},
)
class ApplicationOperationSyncSyncStrategyHook:
    def __init__(self, *, force: typing.Optional[builtins.bool] = None) -> None:
        '''Hook will submit any referenced resources to perform the sync.

        This is the default strategy

        :param force: Force indicates whether or not to supply the --force flag to ``kubectl apply``. The --force flag deletes and re-create the resource, when PATCH encounters conflict and has retried for 5 times.

        :schema: ApplicationOperationSyncSyncStrategyHook
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__232a28768e1b1149f33f9cc4efb2f315e3722f3c5e4472c896498c818abee5e0)
            check_type(argname="argument force", value=force, expected_type=type_hints["force"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if force is not None:
            self._values["force"] = force

    @builtins.property
    def force(self) -> typing.Optional[builtins.bool]:
        '''Force indicates whether or not to supply the --force flag to ``kubectl apply``.

        The --force flag deletes and re-create the resource, when PATCH encounters conflict and has
        retried for 5 times.

        :schema: ApplicationOperationSyncSyncStrategyHook#force
        '''
        result = self._values.get("force")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationOperationSyncSyncStrategyHook(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationProps",
    jsii_struct_bases=[],
    name_mapping={"metadata": "metadata", "spec": "spec", "operation": "operation"},
)
class ApplicationProps:
    def __init__(
        self,
        *,
        metadata: typing.Union[_cdk8s_d3d9af27.ApiObjectMetadata, typing.Dict[builtins.str, typing.Any]],
        spec: typing.Union["ApplicationSpec", typing.Dict[builtins.str, typing.Any]],
        operation: typing.Optional[typing.Union[ApplicationOperation, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Application is a definition of Application resource.

        :param metadata: 
        :param spec: ApplicationSpec represents desired application state. Contains link to repository with application definition and additional parameters link definition revision.
        :param operation: Operation contains information about a requested or running operation.

        :schema: Application
        '''
        if isinstance(metadata, dict):
            metadata = _cdk8s_d3d9af27.ApiObjectMetadata(**metadata)
        if isinstance(spec, dict):
            spec = ApplicationSpec(**spec)
        if isinstance(operation, dict):
            operation = ApplicationOperation(**operation)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5ca23bf220d592849372e0bd99f10e3ce28c86c57e545253a959e91aed82183a)
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
            check_type(argname="argument spec", value=spec, expected_type=type_hints["spec"])
            check_type(argname="argument operation", value=operation, expected_type=type_hints["operation"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "metadata": metadata,
            "spec": spec,
        }
        if operation is not None:
            self._values["operation"] = operation

    @builtins.property
    def metadata(self) -> _cdk8s_d3d9af27.ApiObjectMetadata:
        '''
        :schema: Application#metadata
        '''
        result = self._values.get("metadata")
        assert result is not None, "Required property 'metadata' is missing"
        return typing.cast(_cdk8s_d3d9af27.ApiObjectMetadata, result)

    @builtins.property
    def spec(self) -> "ApplicationSpec":
        '''ApplicationSpec represents desired application state.

        Contains link to repository with application definition and additional parameters link definition revision.

        :schema: Application#spec
        '''
        result = self._values.get("spec")
        assert result is not None, "Required property 'spec' is missing"
        return typing.cast("ApplicationSpec", result)

    @builtins.property
    def operation(self) -> typing.Optional[ApplicationOperation]:
        '''Operation contains information about a requested or running operation.

        :schema: Application#operation
        '''
        result = self._values.get("operation")
        return typing.cast(typing.Optional[ApplicationOperation], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpec",
    jsii_struct_bases=[],
    name_mapping={
        "destination": "destination",
        "project": "project",
        "ignore_differences": "ignoreDifferences",
        "info": "info",
        "revision_history_limit": "revisionHistoryLimit",
        "source": "source",
        "source_hydrator": "sourceHydrator",
        "sources": "sources",
        "sync_policy": "syncPolicy",
    },
)
class ApplicationSpec:
    def __init__(
        self,
        *,
        destination: typing.Union["ApplicationSpecDestination", typing.Dict[builtins.str, typing.Any]],
        project: builtins.str,
        ignore_differences: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecIgnoreDifferences", typing.Dict[builtins.str, typing.Any]]]] = None,
        info: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecInfo", typing.Dict[builtins.str, typing.Any]]]] = None,
        revision_history_limit: typing.Optional[jsii.Number] = None,
        source: typing.Optional[typing.Union["ApplicationSpecSource", typing.Dict[builtins.str, typing.Any]]] = None,
        source_hydrator: typing.Optional[typing.Union["ApplicationSpecSourceHydrator", typing.Dict[builtins.str, typing.Any]]] = None,
        sources: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSources", typing.Dict[builtins.str, typing.Any]]]] = None,
        sync_policy: typing.Optional[typing.Union["ApplicationSpecSyncPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''ApplicationSpec represents desired application state.

        Contains link to repository with application definition and additional parameters link definition revision.

        :param destination: Destination is a reference to the target Kubernetes server and namespace.
        :param project: Project is a reference to the project this application belongs to. The empty string means that application belongs to the 'default' project.
        :param ignore_differences: IgnoreDifferences is a list of resources and their fields which should be ignored during comparison.
        :param info: Info contains a list of information (URLs, email addresses, and plain text) that relates to the application.
        :param revision_history_limit: RevisionHistoryLimit limits the number of items kept in the application's revision history, which is used for informational purposes as well as for rollbacks to previous versions. This should only be changed in exceptional circumstances. Setting to zero will store no history. This will reduce storage used. Increasing will increase the space used to store the history, so we do not recommend increasing it. Default is 10. Default: 10.
        :param source: Source is a reference to the location of the application's manifests or chart.
        :param source_hydrator: SourceHydrator provides a way to push hydrated manifests back to git before syncing them to the cluster.
        :param sources: Sources is a reference to the location of the application's manifests or chart.
        :param sync_policy: SyncPolicy controls when and how a sync will be performed.

        :schema: ApplicationSpec
        '''
        if isinstance(destination, dict):
            destination = ApplicationSpecDestination(**destination)
        if isinstance(source, dict):
            source = ApplicationSpecSource(**source)
        if isinstance(source_hydrator, dict):
            source_hydrator = ApplicationSpecSourceHydrator(**source_hydrator)
        if isinstance(sync_policy, dict):
            sync_policy = ApplicationSpecSyncPolicy(**sync_policy)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a1f307d49d2573da0fdf411f65384f1f5e43cfe5199a85fa3476e965a2efcc9f)
            check_type(argname="argument destination", value=destination, expected_type=type_hints["destination"])
            check_type(argname="argument project", value=project, expected_type=type_hints["project"])
            check_type(argname="argument ignore_differences", value=ignore_differences, expected_type=type_hints["ignore_differences"])
            check_type(argname="argument info", value=info, expected_type=type_hints["info"])
            check_type(argname="argument revision_history_limit", value=revision_history_limit, expected_type=type_hints["revision_history_limit"])
            check_type(argname="argument source", value=source, expected_type=type_hints["source"])
            check_type(argname="argument source_hydrator", value=source_hydrator, expected_type=type_hints["source_hydrator"])
            check_type(argname="argument sources", value=sources, expected_type=type_hints["sources"])
            check_type(argname="argument sync_policy", value=sync_policy, expected_type=type_hints["sync_policy"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "destination": destination,
            "project": project,
        }
        if ignore_differences is not None:
            self._values["ignore_differences"] = ignore_differences
        if info is not None:
            self._values["info"] = info
        if revision_history_limit is not None:
            self._values["revision_history_limit"] = revision_history_limit
        if source is not None:
            self._values["source"] = source
        if source_hydrator is not None:
            self._values["source_hydrator"] = source_hydrator
        if sources is not None:
            self._values["sources"] = sources
        if sync_policy is not None:
            self._values["sync_policy"] = sync_policy

    @builtins.property
    def destination(self) -> "ApplicationSpecDestination":
        '''Destination is a reference to the target Kubernetes server and namespace.

        :schema: ApplicationSpec#destination
        '''
        result = self._values.get("destination")
        assert result is not None, "Required property 'destination' is missing"
        return typing.cast("ApplicationSpecDestination", result)

    @builtins.property
    def project(self) -> builtins.str:
        '''Project is a reference to the project this application belongs to.

        The empty string means that application belongs to the 'default' project.

        :schema: ApplicationSpec#project
        '''
        result = self._values.get("project")
        assert result is not None, "Required property 'project' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ignore_differences(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecIgnoreDifferences"]]:
        '''IgnoreDifferences is a list of resources and their fields which should be ignored during comparison.

        :schema: ApplicationSpec#ignoreDifferences
        '''
        result = self._values.get("ignore_differences")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecIgnoreDifferences"]], result)

    @builtins.property
    def info(self) -> typing.Optional[typing.List["ApplicationSpecInfo"]]:
        '''Info contains a list of information (URLs, email addresses, and plain text) that relates to the application.

        :schema: ApplicationSpec#info
        '''
        result = self._values.get("info")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecInfo"]], result)

    @builtins.property
    def revision_history_limit(self) -> typing.Optional[jsii.Number]:
        '''RevisionHistoryLimit limits the number of items kept in the application's revision history, which is used for informational purposes as well as for rollbacks to previous versions.

        This should only be changed in exceptional circumstances.
        Setting to zero will store no history. This will reduce storage used.
        Increasing will increase the space used to store the history, so we do not recommend increasing it.
        Default is 10.

        :default: 10.

        :schema: ApplicationSpec#revisionHistoryLimit
        '''
        result = self._values.get("revision_history_limit")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def source(self) -> typing.Optional["ApplicationSpecSource"]:
        '''Source is a reference to the location of the application's manifests or chart.

        :schema: ApplicationSpec#source
        '''
        result = self._values.get("source")
        return typing.cast(typing.Optional["ApplicationSpecSource"], result)

    @builtins.property
    def source_hydrator(self) -> typing.Optional["ApplicationSpecSourceHydrator"]:
        '''SourceHydrator provides a way to push hydrated manifests back to git before syncing them to the cluster.

        :schema: ApplicationSpec#sourceHydrator
        '''
        result = self._values.get("source_hydrator")
        return typing.cast(typing.Optional["ApplicationSpecSourceHydrator"], result)

    @builtins.property
    def sources(self) -> typing.Optional[typing.List["ApplicationSpecSources"]]:
        '''Sources is a reference to the location of the application's manifests or chart.

        :schema: ApplicationSpec#sources
        '''
        result = self._values.get("sources")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSources"]], result)

    @builtins.property
    def sync_policy(self) -> typing.Optional["ApplicationSpecSyncPolicy"]:
        '''SyncPolicy controls when and how a sync will be performed.

        :schema: ApplicationSpec#syncPolicy
        '''
        result = self._values.get("sync_policy")
        return typing.cast(typing.Optional["ApplicationSpecSyncPolicy"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpec(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecDestination",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "namespace": "namespace", "server": "server"},
)
class ApplicationSpecDestination:
    def __init__(
        self,
        *,
        name: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        server: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Destination is a reference to the target Kubernetes server and namespace.

        :param name: Name is an alternate way of specifying the target cluster by its symbolic name. This must be set if Server is not set.
        :param namespace: Namespace specifies the target namespace for the application's resources. The namespace will only be set for namespace-scoped resources that have not set a value for .metadata.namespace
        :param server: Server specifies the URL of the target cluster's Kubernetes control plane API. This must be set if Name is not set.

        :schema: ApplicationSpecDestination
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9238a4351184347c423d2fe1d83049e3b26008d848bd55db0649cec36ea400cc)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument server", value=server, expected_type=type_hints["server"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if name is not None:
            self._values["name"] = name
        if namespace is not None:
            self._values["namespace"] = namespace
        if server is not None:
            self._values["server"] = server

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is an alternate way of specifying the target cluster by its symbolic name.

        This must be set if Server is not set.

        :schema: ApplicationSpecDestination#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace specifies the target namespace for the application's resources.

        The namespace will only be set for namespace-scoped resources that have not set a value for .metadata.namespace

        :schema: ApplicationSpecDestination#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def server(self) -> typing.Optional[builtins.str]:
        '''Server specifies the URL of the target cluster's Kubernetes control plane API.

        This must be set if Name is not set.

        :schema: ApplicationSpecDestination#server
        '''
        result = self._values.get("server")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecDestination(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecIgnoreDifferences",
    jsii_struct_bases=[],
    name_mapping={
        "kind": "kind",
        "group": "group",
        "jq_path_expressions": "jqPathExpressions",
        "json_pointers": "jsonPointers",
        "managed_fields_managers": "managedFieldsManagers",
        "name": "name",
        "namespace": "namespace",
    },
)
class ApplicationSpecIgnoreDifferences:
    def __init__(
        self,
        *,
        kind: builtins.str,
        group: typing.Optional[builtins.str] = None,
        jq_path_expressions: typing.Optional[typing.Sequence[builtins.str]] = None,
        json_pointers: typing.Optional[typing.Sequence[builtins.str]] = None,
        managed_fields_managers: typing.Optional[typing.Sequence[builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
    ) -> None:
        '''ResourceIgnoreDifferences contains resource filter and list of json paths which should be ignored during comparison with live state.

        :param kind: 
        :param group: 
        :param jq_path_expressions: 
        :param json_pointers: 
        :param managed_fields_managers: ManagedFieldsManagers is a list of trusted managers. Fields mutated by those managers will take precedence over the desired state defined in the SCM and won't be displayed in diffs
        :param name: 
        :param namespace: 

        :schema: ApplicationSpecIgnoreDifferences
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__574c58e871387b541eae3bcf761bc3c157e86a493ef79d8c8c05cc54c889338b)
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument group", value=group, expected_type=type_hints["group"])
            check_type(argname="argument jq_path_expressions", value=jq_path_expressions, expected_type=type_hints["jq_path_expressions"])
            check_type(argname="argument json_pointers", value=json_pointers, expected_type=type_hints["json_pointers"])
            check_type(argname="argument managed_fields_managers", value=managed_fields_managers, expected_type=type_hints["managed_fields_managers"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "kind": kind,
        }
        if group is not None:
            self._values["group"] = group
        if jq_path_expressions is not None:
            self._values["jq_path_expressions"] = jq_path_expressions
        if json_pointers is not None:
            self._values["json_pointers"] = json_pointers
        if managed_fields_managers is not None:
            self._values["managed_fields_managers"] = managed_fields_managers
        if name is not None:
            self._values["name"] = name
        if namespace is not None:
            self._values["namespace"] = namespace

    @builtins.property
    def kind(self) -> builtins.str:
        '''
        :schema: ApplicationSpecIgnoreDifferences#kind
        '''
        result = self._values.get("kind")
        assert result is not None, "Required property 'kind' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def group(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecIgnoreDifferences#group
        '''
        result = self._values.get("group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jq_path_expressions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''
        :schema: ApplicationSpecIgnoreDifferences#jqPathExpressions
        '''
        result = self._values.get("jq_path_expressions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def json_pointers(self) -> typing.Optional[typing.List[builtins.str]]:
        '''
        :schema: ApplicationSpecIgnoreDifferences#jsonPointers
        '''
        result = self._values.get("json_pointers")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def managed_fields_managers(self) -> typing.Optional[typing.List[builtins.str]]:
        '''ManagedFieldsManagers is a list of trusted managers.

        Fields mutated by those managers will take precedence over the
        desired state defined in the SCM and won't be displayed in diffs

        :schema: ApplicationSpecIgnoreDifferences#managedFieldsManagers
        '''
        result = self._values.get("managed_fields_managers")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecIgnoreDifferences#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecIgnoreDifferences#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecIgnoreDifferences(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecInfo",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value"},
)
class ApplicationSpecInfo:
    def __init__(self, *, name: builtins.str, value: builtins.str) -> None:
        '''
        :param name: 
        :param value: 

        :schema: ApplicationSpecInfo
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__61d3a998a82bb4d85a0cbfb424d45a51c96c47eb4b834a2c399bf783d175a647)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationSpecInfo#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationSpecInfo#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecInfo(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSource",
    jsii_struct_bases=[],
    name_mapping={
        "repo_url": "repoUrl",
        "chart": "chart",
        "directory": "directory",
        "helm": "helm",
        "kustomize": "kustomize",
        "name": "name",
        "path": "path",
        "plugin": "plugin",
        "ref": "ref",
        "target_revision": "targetRevision",
    },
)
class ApplicationSpecSource:
    def __init__(
        self,
        *,
        repo_url: builtins.str,
        chart: typing.Optional[builtins.str] = None,
        directory: typing.Optional[typing.Union["ApplicationSpecSourceDirectory", typing.Dict[builtins.str, typing.Any]]] = None,
        helm: typing.Optional[typing.Union["ApplicationSpecSourceHelm", typing.Dict[builtins.str, typing.Any]]] = None,
        kustomize: typing.Optional[typing.Union["ApplicationSpecSourceKustomize", typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        plugin: typing.Optional[typing.Union["ApplicationSpecSourcePlugin", typing.Dict[builtins.str, typing.Any]]] = None,
        ref: typing.Optional[builtins.str] = None,
        target_revision: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Source is a reference to the location of the application's manifests or chart.

        :param repo_url: RepoURL is the URL to the repository (Git or Helm) that contains the application manifests.
        :param chart: Chart is a Helm chart name, and must be specified for applications sourced from a Helm repo.
        :param directory: Directory holds path/directory specific options.
        :param helm: Helm holds helm specific options.
        :param kustomize: Kustomize holds kustomize specific options.
        :param name: Name is used to refer to a source and is displayed in the UI. It is used in multi-source Applications.
        :param path: Path is a directory path within the Git repository, and is only valid for applications sourced from Git.
        :param plugin: Plugin holds config management plugin specific options.
        :param ref: Ref is reference to another source within sources field. This field will not be used if used with a ``source`` tag.
        :param target_revision: TargetRevision defines the revision of the source to sync the application to. In case of Git, this can be commit, tag, or branch. If omitted, will equal to HEAD. In case of Helm, this is a semver tag for the Chart's version.

        :schema: ApplicationSpecSource
        '''
        if isinstance(directory, dict):
            directory = ApplicationSpecSourceDirectory(**directory)
        if isinstance(helm, dict):
            helm = ApplicationSpecSourceHelm(**helm)
        if isinstance(kustomize, dict):
            kustomize = ApplicationSpecSourceKustomize(**kustomize)
        if isinstance(plugin, dict):
            plugin = ApplicationSpecSourcePlugin(**plugin)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9e157c6d056b54b1b5d1fbf7e83e1fc4beeddb70bdce85c5f9d6a7eefb0b149f)
            check_type(argname="argument repo_url", value=repo_url, expected_type=type_hints["repo_url"])
            check_type(argname="argument chart", value=chart, expected_type=type_hints["chart"])
            check_type(argname="argument directory", value=directory, expected_type=type_hints["directory"])
            check_type(argname="argument helm", value=helm, expected_type=type_hints["helm"])
            check_type(argname="argument kustomize", value=kustomize, expected_type=type_hints["kustomize"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument plugin", value=plugin, expected_type=type_hints["plugin"])
            check_type(argname="argument ref", value=ref, expected_type=type_hints["ref"])
            check_type(argname="argument target_revision", value=target_revision, expected_type=type_hints["target_revision"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "repo_url": repo_url,
        }
        if chart is not None:
            self._values["chart"] = chart
        if directory is not None:
            self._values["directory"] = directory
        if helm is not None:
            self._values["helm"] = helm
        if kustomize is not None:
            self._values["kustomize"] = kustomize
        if name is not None:
            self._values["name"] = name
        if path is not None:
            self._values["path"] = path
        if plugin is not None:
            self._values["plugin"] = plugin
        if ref is not None:
            self._values["ref"] = ref
        if target_revision is not None:
            self._values["target_revision"] = target_revision

    @builtins.property
    def repo_url(self) -> builtins.str:
        '''RepoURL is the URL to the repository (Git or Helm) that contains the application manifests.

        :schema: ApplicationSpecSource#repoURL
        '''
        result = self._values.get("repo_url")
        assert result is not None, "Required property 'repo_url' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def chart(self) -> typing.Optional[builtins.str]:
        '''Chart is a Helm chart name, and must be specified for applications sourced from a Helm repo.

        :schema: ApplicationSpecSource#chart
        '''
        result = self._values.get("chart")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def directory(self) -> typing.Optional["ApplicationSpecSourceDirectory"]:
        '''Directory holds path/directory specific options.

        :schema: ApplicationSpecSource#directory
        '''
        result = self._values.get("directory")
        return typing.cast(typing.Optional["ApplicationSpecSourceDirectory"], result)

    @builtins.property
    def helm(self) -> typing.Optional["ApplicationSpecSourceHelm"]:
        '''Helm holds helm specific options.

        :schema: ApplicationSpecSource#helm
        '''
        result = self._values.get("helm")
        return typing.cast(typing.Optional["ApplicationSpecSourceHelm"], result)

    @builtins.property
    def kustomize(self) -> typing.Optional["ApplicationSpecSourceKustomize"]:
        '''Kustomize holds kustomize specific options.

        :schema: ApplicationSpecSource#kustomize
        '''
        result = self._values.get("kustomize")
        return typing.cast(typing.Optional["ApplicationSpecSourceKustomize"], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is used to refer to a source and is displayed in the UI.

        It is used in multi-source Applications.

        :schema: ApplicationSpecSource#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Path is a directory path within the Git repository, and is only valid for applications sourced from Git.

        :schema: ApplicationSpecSource#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def plugin(self) -> typing.Optional["ApplicationSpecSourcePlugin"]:
        '''Plugin holds config management plugin specific options.

        :schema: ApplicationSpecSource#plugin
        '''
        result = self._values.get("plugin")
        return typing.cast(typing.Optional["ApplicationSpecSourcePlugin"], result)

    @builtins.property
    def ref(self) -> typing.Optional[builtins.str]:
        '''Ref is reference to another source within sources field.

        This field will not be used if used with a ``source`` tag.

        :schema: ApplicationSpecSource#ref
        '''
        result = self._values.get("ref")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_revision(self) -> typing.Optional[builtins.str]:
        '''TargetRevision defines the revision of the source to sync the application to.

        In case of Git, this can be commit, tag, or branch. If omitted, will equal to HEAD.
        In case of Helm, this is a semver tag for the Chart's version.

        :schema: ApplicationSpecSource#targetRevision
        '''
        result = self._values.get("target_revision")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceDirectory",
    jsii_struct_bases=[],
    name_mapping={
        "exclude": "exclude",
        "include": "include",
        "jsonnet": "jsonnet",
        "recurse": "recurse",
    },
)
class ApplicationSpecSourceDirectory:
    def __init__(
        self,
        *,
        exclude: typing.Optional[builtins.str] = None,
        include: typing.Optional[builtins.str] = None,
        jsonnet: typing.Optional[typing.Union["ApplicationSpecSourceDirectoryJsonnet", typing.Dict[builtins.str, typing.Any]]] = None,
        recurse: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Directory holds path/directory specific options.

        :param exclude: Exclude contains a glob pattern to match paths against that should be explicitly excluded from being used during manifest generation.
        :param include: Include contains a glob pattern to match paths against that should be explicitly included during manifest generation.
        :param jsonnet: Jsonnet holds options specific to Jsonnet.
        :param recurse: Recurse specifies whether to scan a directory recursively for manifests.

        :schema: ApplicationSpecSourceDirectory
        '''
        if isinstance(jsonnet, dict):
            jsonnet = ApplicationSpecSourceDirectoryJsonnet(**jsonnet)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fefb1318b48ea3fb382bc321682e8a64abdc9207410353cc534e21613fdb026e)
            check_type(argname="argument exclude", value=exclude, expected_type=type_hints["exclude"])
            check_type(argname="argument include", value=include, expected_type=type_hints["include"])
            check_type(argname="argument jsonnet", value=jsonnet, expected_type=type_hints["jsonnet"])
            check_type(argname="argument recurse", value=recurse, expected_type=type_hints["recurse"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if exclude is not None:
            self._values["exclude"] = exclude
        if include is not None:
            self._values["include"] = include
        if jsonnet is not None:
            self._values["jsonnet"] = jsonnet
        if recurse is not None:
            self._values["recurse"] = recurse

    @builtins.property
    def exclude(self) -> typing.Optional[builtins.str]:
        '''Exclude contains a glob pattern to match paths against that should be explicitly excluded from being used during manifest generation.

        :schema: ApplicationSpecSourceDirectory#exclude
        '''
        result = self._values.get("exclude")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def include(self) -> typing.Optional[builtins.str]:
        '''Include contains a glob pattern to match paths against that should be explicitly included during manifest generation.

        :schema: ApplicationSpecSourceDirectory#include
        '''
        result = self._values.get("include")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jsonnet(self) -> typing.Optional["ApplicationSpecSourceDirectoryJsonnet"]:
        '''Jsonnet holds options specific to Jsonnet.

        :schema: ApplicationSpecSourceDirectory#jsonnet
        '''
        result = self._values.get("jsonnet")
        return typing.cast(typing.Optional["ApplicationSpecSourceDirectoryJsonnet"], result)

    @builtins.property
    def recurse(self) -> typing.Optional[builtins.bool]:
        '''Recurse specifies whether to scan a directory recursively for manifests.

        :schema: ApplicationSpecSourceDirectory#recurse
        '''
        result = self._values.get("recurse")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceDirectory(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceDirectoryJsonnet",
    jsii_struct_bases=[],
    name_mapping={"ext_vars": "extVars", "libs": "libs", "tlas": "tlas"},
)
class ApplicationSpecSourceDirectoryJsonnet:
    def __init__(
        self,
        *,
        ext_vars: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourceDirectoryJsonnetExtVars", typing.Dict[builtins.str, typing.Any]]]] = None,
        libs: typing.Optional[typing.Sequence[builtins.str]] = None,
        tlas: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourceDirectoryJsonnetTlas", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Jsonnet holds options specific to Jsonnet.

        :param ext_vars: ExtVars is a list of Jsonnet External Variables.
        :param libs: Additional library search dirs.
        :param tlas: TLAS is a list of Jsonnet Top-level Arguments.

        :schema: ApplicationSpecSourceDirectoryJsonnet
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1d9ee2168d505513d2adfe23f15ef2bd0f287cc883a3bed308c75211a57ddaf2)
            check_type(argname="argument ext_vars", value=ext_vars, expected_type=type_hints["ext_vars"])
            check_type(argname="argument libs", value=libs, expected_type=type_hints["libs"])
            check_type(argname="argument tlas", value=tlas, expected_type=type_hints["tlas"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if ext_vars is not None:
            self._values["ext_vars"] = ext_vars
        if libs is not None:
            self._values["libs"] = libs
        if tlas is not None:
            self._values["tlas"] = tlas

    @builtins.property
    def ext_vars(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourceDirectoryJsonnetExtVars"]]:
        '''ExtVars is a list of Jsonnet External Variables.

        :schema: ApplicationSpecSourceDirectoryJsonnet#extVars
        '''
        result = self._values.get("ext_vars")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourceDirectoryJsonnetExtVars"]], result)

    @builtins.property
    def libs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Additional library search dirs.

        :schema: ApplicationSpecSourceDirectoryJsonnet#libs
        '''
        result = self._values.get("libs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def tlas(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourceDirectoryJsonnetTlas"]]:
        '''TLAS is a list of Jsonnet Top-level Arguments.

        :schema: ApplicationSpecSourceDirectoryJsonnet#tlas
        '''
        result = self._values.get("tlas")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourceDirectoryJsonnetTlas"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceDirectoryJsonnet(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceDirectoryJsonnetExtVars",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value", "code": "code"},
)
class ApplicationSpecSourceDirectoryJsonnetExtVars:
    def __init__(
        self,
        *,
        name: builtins.str,
        value: builtins.str,
        code: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''JsonnetVar represents a variable to be passed to jsonnet during manifest generation.

        :param name: 
        :param value: 
        :param code: 

        :schema: ApplicationSpecSourceDirectoryJsonnetExtVars
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e483cf00940264ac67776c440bb705233ad665f91518ff22fd686da8e5fa920d)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument code", value=code, expected_type=type_hints["code"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }
        if code is not None:
            self._values["code"] = code

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationSpecSourceDirectoryJsonnetExtVars#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationSpecSourceDirectoryJsonnetExtVars#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def code(self) -> typing.Optional[builtins.bool]:
        '''
        :schema: ApplicationSpecSourceDirectoryJsonnetExtVars#code
        '''
        result = self._values.get("code")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceDirectoryJsonnetExtVars(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceDirectoryJsonnetTlas",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value", "code": "code"},
)
class ApplicationSpecSourceDirectoryJsonnetTlas:
    def __init__(
        self,
        *,
        name: builtins.str,
        value: builtins.str,
        code: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''JsonnetVar represents a variable to be passed to jsonnet during manifest generation.

        :param name: 
        :param value: 
        :param code: 

        :schema: ApplicationSpecSourceDirectoryJsonnetTlas
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__23a8df3f1e29d28a29abd9689aaca70ce6d998c6b6a143470b15e0bb4bcde305)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument code", value=code, expected_type=type_hints["code"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }
        if code is not None:
            self._values["code"] = code

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationSpecSourceDirectoryJsonnetTlas#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationSpecSourceDirectoryJsonnetTlas#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def code(self) -> typing.Optional[builtins.bool]:
        '''
        :schema: ApplicationSpecSourceDirectoryJsonnetTlas#code
        '''
        result = self._values.get("code")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceDirectoryJsonnetTlas(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceHelm",
    jsii_struct_bases=[],
    name_mapping={
        "api_versions": "apiVersions",
        "file_parameters": "fileParameters",
        "ignore_missing_value_files": "ignoreMissingValueFiles",
        "kube_version": "kubeVersion",
        "namespace": "namespace",
        "parameters": "parameters",
        "pass_credentials": "passCredentials",
        "release_name": "releaseName",
        "skip_crds": "skipCrds",
        "skip_schema_validation": "skipSchemaValidation",
        "skip_tests": "skipTests",
        "value_files": "valueFiles",
        "values": "values",
        "values_object": "valuesObject",
        "version": "version",
    },
)
class ApplicationSpecSourceHelm:
    def __init__(
        self,
        *,
        api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
        file_parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourceHelmFileParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_missing_value_files: typing.Optional[builtins.bool] = None,
        kube_version: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourceHelmParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
        pass_credentials: typing.Optional[builtins.bool] = None,
        release_name: typing.Optional[builtins.str] = None,
        skip_crds: typing.Optional[builtins.bool] = None,
        skip_schema_validation: typing.Optional[builtins.bool] = None,
        skip_tests: typing.Optional[builtins.bool] = None,
        value_files: typing.Optional[typing.Sequence[builtins.str]] = None,
        values: typing.Optional[builtins.str] = None,
        values_object: typing.Any = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Helm holds helm specific options.

        :param api_versions: APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests. By default, Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.
        :param file_parameters: FileParameters are file parameters to the helm template.
        :param ignore_missing_value_files: IgnoreMissingValueFiles prevents helm template from failing when valueFiles do not exist locally by not appending them to helm template --values.
        :param kube_version: KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests. By default, Argo CD uses the Kubernetes version of the target cluster.
        :param namespace: Namespace is an optional namespace to template with. If left empty, defaults to the app's destination namespace.
        :param parameters: Parameters is a list of Helm parameters which are passed to the helm template command upon manifest generation.
        :param pass_credentials: PassCredentials pass credentials to all domains (Helm's --pass-credentials).
        :param release_name: ReleaseName is the Helm release name to use. If omitted it will use the application name
        :param skip_crds: SkipCrds skips custom resource definition installation step (Helm's --skip-crds).
        :param skip_schema_validation: SkipSchemaValidation skips JSON schema validation (Helm's --skip-schema-validation).
        :param skip_tests: SkipTests skips test manifest installation step (Helm's --skip-tests).
        :param value_files: ValuesFiles is a list of Helm value files to use when generating a template.
        :param values: Values specifies Helm values to be passed to helm template, typically defined as a block. ValuesObject takes precedence over Values, so use one or the other.
        :param values_object: ValuesObject specifies Helm values to be passed to helm template, defined as a map. This takes precedence over Values.
        :param version: Version is the Helm version to use for templating ("3").

        :schema: ApplicationSpecSourceHelm
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c8e613a2adc9ba39f281a30a94252f51b6222660f9b4ffddfbe53ea8e6648238)
            check_type(argname="argument api_versions", value=api_versions, expected_type=type_hints["api_versions"])
            check_type(argname="argument file_parameters", value=file_parameters, expected_type=type_hints["file_parameters"])
            check_type(argname="argument ignore_missing_value_files", value=ignore_missing_value_files, expected_type=type_hints["ignore_missing_value_files"])
            check_type(argname="argument kube_version", value=kube_version, expected_type=type_hints["kube_version"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
            check_type(argname="argument pass_credentials", value=pass_credentials, expected_type=type_hints["pass_credentials"])
            check_type(argname="argument release_name", value=release_name, expected_type=type_hints["release_name"])
            check_type(argname="argument skip_crds", value=skip_crds, expected_type=type_hints["skip_crds"])
            check_type(argname="argument skip_schema_validation", value=skip_schema_validation, expected_type=type_hints["skip_schema_validation"])
            check_type(argname="argument skip_tests", value=skip_tests, expected_type=type_hints["skip_tests"])
            check_type(argname="argument value_files", value=value_files, expected_type=type_hints["value_files"])
            check_type(argname="argument values", value=values, expected_type=type_hints["values"])
            check_type(argname="argument values_object", value=values_object, expected_type=type_hints["values_object"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_versions is not None:
            self._values["api_versions"] = api_versions
        if file_parameters is not None:
            self._values["file_parameters"] = file_parameters
        if ignore_missing_value_files is not None:
            self._values["ignore_missing_value_files"] = ignore_missing_value_files
        if kube_version is not None:
            self._values["kube_version"] = kube_version
        if namespace is not None:
            self._values["namespace"] = namespace
        if parameters is not None:
            self._values["parameters"] = parameters
        if pass_credentials is not None:
            self._values["pass_credentials"] = pass_credentials
        if release_name is not None:
            self._values["release_name"] = release_name
        if skip_crds is not None:
            self._values["skip_crds"] = skip_crds
        if skip_schema_validation is not None:
            self._values["skip_schema_validation"] = skip_schema_validation
        if skip_tests is not None:
            self._values["skip_tests"] = skip_tests
        if value_files is not None:
            self._values["value_files"] = value_files
        if values is not None:
            self._values["values"] = values
        if values_object is not None:
            self._values["values_object"] = values_object
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def api_versions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests.

        By default,
        Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.

        :schema: ApplicationSpecSourceHelm#apiVersions
        '''
        result = self._values.get("api_versions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def file_parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourceHelmFileParameters"]]:
        '''FileParameters are file parameters to the helm template.

        :schema: ApplicationSpecSourceHelm#fileParameters
        '''
        result = self._values.get("file_parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourceHelmFileParameters"]], result)

    @builtins.property
    def ignore_missing_value_files(self) -> typing.Optional[builtins.bool]:
        '''IgnoreMissingValueFiles prevents helm template from failing when valueFiles do not exist locally by not appending them to helm template --values.

        :schema: ApplicationSpecSourceHelm#ignoreMissingValueFiles
        '''
        result = self._values.get("ignore_missing_value_files")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def kube_version(self) -> typing.Optional[builtins.str]:
        '''KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests.

        By default, Argo CD
        uses the Kubernetes version of the target cluster.

        :schema: ApplicationSpecSourceHelm#kubeVersion
        '''
        result = self._values.get("kube_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace is an optional namespace to template with.

        If left empty, defaults to the app's destination namespace.

        :schema: ApplicationSpecSourceHelm#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourceHelmParameters"]]:
        '''Parameters is a list of Helm parameters which are passed to the helm template command upon manifest generation.

        :schema: ApplicationSpecSourceHelm#parameters
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourceHelmParameters"]], result)

    @builtins.property
    def pass_credentials(self) -> typing.Optional[builtins.bool]:
        '''PassCredentials pass credentials to all domains (Helm's --pass-credentials).

        :schema: ApplicationSpecSourceHelm#passCredentials
        '''
        result = self._values.get("pass_credentials")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_name(self) -> typing.Optional[builtins.str]:
        '''ReleaseName is the Helm release name to use.

        If omitted it will use the application name

        :schema: ApplicationSpecSourceHelm#releaseName
        '''
        result = self._values.get("release_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def skip_crds(self) -> typing.Optional[builtins.bool]:
        '''SkipCrds skips custom resource definition installation step (Helm's --skip-crds).

        :schema: ApplicationSpecSourceHelm#skipCrds
        '''
        result = self._values.get("skip_crds")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip_schema_validation(self) -> typing.Optional[builtins.bool]:
        '''SkipSchemaValidation skips JSON schema validation (Helm's --skip-schema-validation).

        :schema: ApplicationSpecSourceHelm#skipSchemaValidation
        '''
        result = self._values.get("skip_schema_validation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip_tests(self) -> typing.Optional[builtins.bool]:
        '''SkipTests skips test manifest installation step (Helm's --skip-tests).

        :schema: ApplicationSpecSourceHelm#skipTests
        '''
        result = self._values.get("skip_tests")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def value_files(self) -> typing.Optional[typing.List[builtins.str]]:
        '''ValuesFiles is a list of Helm value files to use when generating a template.

        :schema: ApplicationSpecSourceHelm#valueFiles
        '''
        result = self._values.get("value_files")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def values(self) -> typing.Optional[builtins.str]:
        '''Values specifies Helm values to be passed to helm template, typically defined as a block.

        ValuesObject takes precedence over Values, so use one or the other.

        :schema: ApplicationSpecSourceHelm#values
        '''
        result = self._values.get("values")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def values_object(self) -> typing.Any:
        '''ValuesObject specifies Helm values to be passed to helm template, defined as a map.

        This takes precedence over Values.

        :schema: ApplicationSpecSourceHelm#valuesObject
        '''
        result = self._values.get("values_object")
        return typing.cast(typing.Any, result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version is the Helm version to use for templating ("3").

        :schema: ApplicationSpecSourceHelm#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceHelm(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceHelmFileParameters",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "path": "path"},
)
class ApplicationSpecSourceHelmFileParameters:
    def __init__(
        self,
        *,
        name: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HelmFileParameter is a file parameter that's passed to helm template during manifest generation.

        :param name: Name is the name of the Helm parameter.
        :param path: Path is the path to the file containing the values for the Helm parameter.

        :schema: ApplicationSpecSourceHelmFileParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8346dcda3d2bf59be52a4b4202b835794b0570f15154850d4a7a89ed67e802e1)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if name is not None:
            self._values["name"] = name
        if path is not None:
            self._values["path"] = path

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name of the Helm parameter.

        :schema: ApplicationSpecSourceHelmFileParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Path is the path to the file containing the values for the Helm parameter.

        :schema: ApplicationSpecSourceHelmFileParameters#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceHelmFileParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceHelmParameters",
    jsii_struct_bases=[],
    name_mapping={"force_string": "forceString", "name": "name", "value": "value"},
)
class ApplicationSpecSourceHelmParameters:
    def __init__(
        self,
        *,
        force_string: typing.Optional[builtins.bool] = None,
        name: typing.Optional[builtins.str] = None,
        value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HelmParameter is a parameter that's passed to helm template during manifest generation.

        :param force_string: ForceString determines whether to tell Helm to interpret booleans and numbers as strings.
        :param name: Name is the name of the Helm parameter.
        :param value: Value is the value for the Helm parameter.

        :schema: ApplicationSpecSourceHelmParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__17a5ce92a0f0e0c91bd2a36e1146c8eabaa0b69b93d5fb75fdeaf97cd1d288b5)
            check_type(argname="argument force_string", value=force_string, expected_type=type_hints["force_string"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if force_string is not None:
            self._values["force_string"] = force_string
        if name is not None:
            self._values["name"] = name
        if value is not None:
            self._values["value"] = value

    @builtins.property
    def force_string(self) -> typing.Optional[builtins.bool]:
        '''ForceString determines whether to tell Helm to interpret booleans and numbers as strings.

        :schema: ApplicationSpecSourceHelmParameters#forceString
        '''
        result = self._values.get("force_string")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name of the Helm parameter.

        :schema: ApplicationSpecSourceHelmParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def value(self) -> typing.Optional[builtins.str]:
        '''Value is the value for the Helm parameter.

        :schema: ApplicationSpecSourceHelmParameters#value
        '''
        result = self._values.get("value")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceHelmParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceHydrator",
    jsii_struct_bases=[],
    name_mapping={
        "dry_source": "drySource",
        "sync_source": "syncSource",
        "hydrate_to": "hydrateTo",
    },
)
class ApplicationSpecSourceHydrator:
    def __init__(
        self,
        *,
        dry_source: typing.Union["ApplicationSpecSourceHydratorDrySource", typing.Dict[builtins.str, typing.Any]],
        sync_source: typing.Union["ApplicationSpecSourceHydratorSyncSource", typing.Dict[builtins.str, typing.Any]],
        hydrate_to: typing.Optional[typing.Union["ApplicationSpecSourceHydratorHydrateTo", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''SourceHydrator provides a way to push hydrated manifests back to git before syncing them to the cluster.

        :param dry_source: DrySource specifies where the dry "don't repeat yourself" manifest source lives.
        :param sync_source: SyncSource specifies where to sync hydrated manifests from.
        :param hydrate_to: HydrateTo specifies an optional "staging" location to push hydrated manifests to. An external system would then have to move manifests to the SyncSource, e.g. by pull request.

        :schema: ApplicationSpecSourceHydrator
        '''
        if isinstance(dry_source, dict):
            dry_source = ApplicationSpecSourceHydratorDrySource(**dry_source)
        if isinstance(sync_source, dict):
            sync_source = ApplicationSpecSourceHydratorSyncSource(**sync_source)
        if isinstance(hydrate_to, dict):
            hydrate_to = ApplicationSpecSourceHydratorHydrateTo(**hydrate_to)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__75adc1cbe17b67a5524593319046518279392ab75ca34ccadb0ea819ac1118e9)
            check_type(argname="argument dry_source", value=dry_source, expected_type=type_hints["dry_source"])
            check_type(argname="argument sync_source", value=sync_source, expected_type=type_hints["sync_source"])
            check_type(argname="argument hydrate_to", value=hydrate_to, expected_type=type_hints["hydrate_to"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "dry_source": dry_source,
            "sync_source": sync_source,
        }
        if hydrate_to is not None:
            self._values["hydrate_to"] = hydrate_to

    @builtins.property
    def dry_source(self) -> "ApplicationSpecSourceHydratorDrySource":
        '''DrySource specifies where the dry "don't repeat yourself" manifest source lives.

        :schema: ApplicationSpecSourceHydrator#drySource
        '''
        result = self._values.get("dry_source")
        assert result is not None, "Required property 'dry_source' is missing"
        return typing.cast("ApplicationSpecSourceHydratorDrySource", result)

    @builtins.property
    def sync_source(self) -> "ApplicationSpecSourceHydratorSyncSource":
        '''SyncSource specifies where to sync hydrated manifests from.

        :schema: ApplicationSpecSourceHydrator#syncSource
        '''
        result = self._values.get("sync_source")
        assert result is not None, "Required property 'sync_source' is missing"
        return typing.cast("ApplicationSpecSourceHydratorSyncSource", result)

    @builtins.property
    def hydrate_to(self) -> typing.Optional["ApplicationSpecSourceHydratorHydrateTo"]:
        '''HydrateTo specifies an optional "staging" location to push hydrated manifests to.

        An external system would then
        have to move manifests to the SyncSource, e.g. by pull request.

        :schema: ApplicationSpecSourceHydrator#hydrateTo
        '''
        result = self._values.get("hydrate_to")
        return typing.cast(typing.Optional["ApplicationSpecSourceHydratorHydrateTo"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceHydrator(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceHydratorDrySource",
    jsii_struct_bases=[],
    name_mapping={
        "path": "path",
        "repo_url": "repoUrl",
        "target_revision": "targetRevision",
    },
)
class ApplicationSpecSourceHydratorDrySource:
    def __init__(
        self,
        *,
        path: builtins.str,
        repo_url: builtins.str,
        target_revision: builtins.str,
    ) -> None:
        '''DrySource specifies where the dry "don't repeat yourself" manifest source lives.

        :param path: Path is a directory path within the Git repository where the manifests are located.
        :param repo_url: RepoURL is the URL to the git repository that contains the application manifests.
        :param target_revision: TargetRevision defines the revision of the source to hydrate.

        :schema: ApplicationSpecSourceHydratorDrySource
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ec68ad68d4119003f20c64caa9dc260c146a7a752b739e50490c695975353cd6)
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument repo_url", value=repo_url, expected_type=type_hints["repo_url"])
            check_type(argname="argument target_revision", value=target_revision, expected_type=type_hints["target_revision"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "path": path,
            "repo_url": repo_url,
            "target_revision": target_revision,
        }

    @builtins.property
    def path(self) -> builtins.str:
        '''Path is a directory path within the Git repository where the manifests are located.

        :schema: ApplicationSpecSourceHydratorDrySource#path
        '''
        result = self._values.get("path")
        assert result is not None, "Required property 'path' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def repo_url(self) -> builtins.str:
        '''RepoURL is the URL to the git repository that contains the application manifests.

        :schema: ApplicationSpecSourceHydratorDrySource#repoURL
        '''
        result = self._values.get("repo_url")
        assert result is not None, "Required property 'repo_url' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def target_revision(self) -> builtins.str:
        '''TargetRevision defines the revision of the source to hydrate.

        :schema: ApplicationSpecSourceHydratorDrySource#targetRevision
        '''
        result = self._values.get("target_revision")
        assert result is not None, "Required property 'target_revision' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceHydratorDrySource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceHydratorHydrateTo",
    jsii_struct_bases=[],
    name_mapping={"target_branch": "targetBranch"},
)
class ApplicationSpecSourceHydratorHydrateTo:
    def __init__(self, *, target_branch: builtins.str) -> None:
        '''HydrateTo specifies an optional "staging" location to push hydrated manifests to.

        An external system would then
        have to move manifests to the SyncSource, e.g. by pull request.

        :param target_branch: TargetBranch is the branch to which hydrated manifests should be committed.

        :schema: ApplicationSpecSourceHydratorHydrateTo
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e970d9eb63dc5fabee5daa8e34fd18483c489f6644799712804d76dab7c380a5)
            check_type(argname="argument target_branch", value=target_branch, expected_type=type_hints["target_branch"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "target_branch": target_branch,
        }

    @builtins.property
    def target_branch(self) -> builtins.str:
        '''TargetBranch is the branch to which hydrated manifests should be committed.

        :schema: ApplicationSpecSourceHydratorHydrateTo#targetBranch
        '''
        result = self._values.get("target_branch")
        assert result is not None, "Required property 'target_branch' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceHydratorHydrateTo(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceHydratorSyncSource",
    jsii_struct_bases=[],
    name_mapping={"path": "path", "target_branch": "targetBranch"},
)
class ApplicationSpecSourceHydratorSyncSource:
    def __init__(self, *, path: builtins.str, target_branch: builtins.str) -> None:
        '''SyncSource specifies where to sync hydrated manifests from.

        :param path: Path is a directory path within the git repository where hydrated manifests should be committed to and synced from. The Path should never point to the root of the repo. If hydrateTo is set, this is just the path from which hydrated manifests will be synced.
        :param target_branch: TargetBranch is the branch from which hydrated manifests will be synced. If HydrateTo is not set, this is also the branch to which hydrated manifests are committed.

        :schema: ApplicationSpecSourceHydratorSyncSource
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__add5badb0c8beefd8c8f5c21ee57af7fc7131958e07635aa1a79cd7f39defc86)
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument target_branch", value=target_branch, expected_type=type_hints["target_branch"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "path": path,
            "target_branch": target_branch,
        }

    @builtins.property
    def path(self) -> builtins.str:
        '''Path is a directory path within the git repository where hydrated manifests should be committed to and synced from.

        The Path should never point to the root of the repo. If hydrateTo is set, this is just the path from which
        hydrated manifests will be synced.

        :schema: ApplicationSpecSourceHydratorSyncSource#path
        '''
        result = self._values.get("path")
        assert result is not None, "Required property 'path' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def target_branch(self) -> builtins.str:
        '''TargetBranch is the branch from which hydrated manifests will be synced.

        If HydrateTo is not set, this is also the branch to which hydrated manifests are committed.

        :schema: ApplicationSpecSourceHydratorSyncSource#targetBranch
        '''
        result = self._values.get("target_branch")
        assert result is not None, "Required property 'target_branch' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceHydratorSyncSource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceKustomize",
    jsii_struct_bases=[],
    name_mapping={
        "api_versions": "apiVersions",
        "common_annotations": "commonAnnotations",
        "common_annotations_envsubst": "commonAnnotationsEnvsubst",
        "common_labels": "commonLabels",
        "components": "components",
        "force_common_annotations": "forceCommonAnnotations",
        "force_common_labels": "forceCommonLabels",
        "ignore_missing_components": "ignoreMissingComponents",
        "images": "images",
        "kube_version": "kubeVersion",
        "label_include_templates": "labelIncludeTemplates",
        "label_without_selector": "labelWithoutSelector",
        "name_prefix": "namePrefix",
        "namespace": "namespace",
        "name_suffix": "nameSuffix",
        "patches": "patches",
        "replicas": "replicas",
        "version": "version",
    },
)
class ApplicationSpecSourceKustomize:
    def __init__(
        self,
        *,
        api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
        common_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        common_annotations_envsubst: typing.Optional[builtins.bool] = None,
        common_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        components: typing.Optional[typing.Sequence[builtins.str]] = None,
        force_common_annotations: typing.Optional[builtins.bool] = None,
        force_common_labels: typing.Optional[builtins.bool] = None,
        ignore_missing_components: typing.Optional[builtins.bool] = None,
        images: typing.Optional[typing.Sequence[builtins.str]] = None,
        kube_version: typing.Optional[builtins.str] = None,
        label_include_templates: typing.Optional[builtins.bool] = None,
        label_without_selector: typing.Optional[builtins.bool] = None,
        name_prefix: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        name_suffix: typing.Optional[builtins.str] = None,
        patches: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourceKustomizePatches", typing.Dict[builtins.str, typing.Any]]]] = None,
        replicas: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourceKustomizeReplicas", typing.Dict[builtins.str, typing.Any]]]] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Kustomize holds kustomize specific options.

        :param api_versions: APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests. By default, Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.
        :param common_annotations: CommonAnnotations is a list of additional annotations to add to rendered manifests.
        :param common_annotations_envsubst: CommonAnnotationsEnvsubst specifies whether to apply env variables substitution for annotation values.
        :param common_labels: CommonLabels is a list of additional labels to add to rendered manifests.
        :param components: Components specifies a list of kustomize components to add to the kustomization before building.
        :param force_common_annotations: ForceCommonAnnotations specifies whether to force applying common annotations to resources for Kustomize apps.
        :param force_common_labels: ForceCommonLabels specifies whether to force applying common labels to resources for Kustomize apps.
        :param ignore_missing_components: IgnoreMissingComponents prevents kustomize from failing when components do not exist locally by not appending them to kustomization file.
        :param images: Images is a list of Kustomize image override specifications.
        :param kube_version: KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests. By default, Argo CD uses the Kubernetes version of the target cluster.
        :param label_include_templates: LabelIncludeTemplates specifies whether to apply common labels to resource templates or not.
        :param label_without_selector: LabelWithoutSelector specifies whether to apply common labels to resource selectors or not.
        :param name_prefix: NamePrefix is a prefix appended to resources for Kustomize apps.
        :param namespace: Namespace sets the namespace that Kustomize adds to all resources.
        :param name_suffix: NameSuffix is a suffix appended to resources for Kustomize apps.
        :param patches: Patches is a list of Kustomize patches.
        :param replicas: Replicas is a list of Kustomize Replicas override specifications.
        :param version: Version controls which version of Kustomize to use for rendering manifests.

        :schema: ApplicationSpecSourceKustomize
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2607d3d54e995cb9b20e089324cc22c5307e97d282257346f223af8e215c526f)
            check_type(argname="argument api_versions", value=api_versions, expected_type=type_hints["api_versions"])
            check_type(argname="argument common_annotations", value=common_annotations, expected_type=type_hints["common_annotations"])
            check_type(argname="argument common_annotations_envsubst", value=common_annotations_envsubst, expected_type=type_hints["common_annotations_envsubst"])
            check_type(argname="argument common_labels", value=common_labels, expected_type=type_hints["common_labels"])
            check_type(argname="argument components", value=components, expected_type=type_hints["components"])
            check_type(argname="argument force_common_annotations", value=force_common_annotations, expected_type=type_hints["force_common_annotations"])
            check_type(argname="argument force_common_labels", value=force_common_labels, expected_type=type_hints["force_common_labels"])
            check_type(argname="argument ignore_missing_components", value=ignore_missing_components, expected_type=type_hints["ignore_missing_components"])
            check_type(argname="argument images", value=images, expected_type=type_hints["images"])
            check_type(argname="argument kube_version", value=kube_version, expected_type=type_hints["kube_version"])
            check_type(argname="argument label_include_templates", value=label_include_templates, expected_type=type_hints["label_include_templates"])
            check_type(argname="argument label_without_selector", value=label_without_selector, expected_type=type_hints["label_without_selector"])
            check_type(argname="argument name_prefix", value=name_prefix, expected_type=type_hints["name_prefix"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument name_suffix", value=name_suffix, expected_type=type_hints["name_suffix"])
            check_type(argname="argument patches", value=patches, expected_type=type_hints["patches"])
            check_type(argname="argument replicas", value=replicas, expected_type=type_hints["replicas"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_versions is not None:
            self._values["api_versions"] = api_versions
        if common_annotations is not None:
            self._values["common_annotations"] = common_annotations
        if common_annotations_envsubst is not None:
            self._values["common_annotations_envsubst"] = common_annotations_envsubst
        if common_labels is not None:
            self._values["common_labels"] = common_labels
        if components is not None:
            self._values["components"] = components
        if force_common_annotations is not None:
            self._values["force_common_annotations"] = force_common_annotations
        if force_common_labels is not None:
            self._values["force_common_labels"] = force_common_labels
        if ignore_missing_components is not None:
            self._values["ignore_missing_components"] = ignore_missing_components
        if images is not None:
            self._values["images"] = images
        if kube_version is not None:
            self._values["kube_version"] = kube_version
        if label_include_templates is not None:
            self._values["label_include_templates"] = label_include_templates
        if label_without_selector is not None:
            self._values["label_without_selector"] = label_without_selector
        if name_prefix is not None:
            self._values["name_prefix"] = name_prefix
        if namespace is not None:
            self._values["namespace"] = namespace
        if name_suffix is not None:
            self._values["name_suffix"] = name_suffix
        if patches is not None:
            self._values["patches"] = patches
        if replicas is not None:
            self._values["replicas"] = replicas
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def api_versions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests.

        By default,
        Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.

        :schema: ApplicationSpecSourceKustomize#apiVersions
        '''
        result = self._values.get("api_versions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def common_annotations(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''CommonAnnotations is a list of additional annotations to add to rendered manifests.

        :schema: ApplicationSpecSourceKustomize#commonAnnotations
        '''
        result = self._values.get("common_annotations")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def common_annotations_envsubst(self) -> typing.Optional[builtins.bool]:
        '''CommonAnnotationsEnvsubst specifies whether to apply env variables substitution for annotation values.

        :schema: ApplicationSpecSourceKustomize#commonAnnotationsEnvsubst
        '''
        result = self._values.get("common_annotations_envsubst")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def common_labels(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''CommonLabels is a list of additional labels to add to rendered manifests.

        :schema: ApplicationSpecSourceKustomize#commonLabels
        '''
        result = self._values.get("common_labels")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def components(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Components specifies a list of kustomize components to add to the kustomization before building.

        :schema: ApplicationSpecSourceKustomize#components
        '''
        result = self._values.get("components")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def force_common_annotations(self) -> typing.Optional[builtins.bool]:
        '''ForceCommonAnnotations specifies whether to force applying common annotations to resources for Kustomize apps.

        :schema: ApplicationSpecSourceKustomize#forceCommonAnnotations
        '''
        result = self._values.get("force_common_annotations")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def force_common_labels(self) -> typing.Optional[builtins.bool]:
        '''ForceCommonLabels specifies whether to force applying common labels to resources for Kustomize apps.

        :schema: ApplicationSpecSourceKustomize#forceCommonLabels
        '''
        result = self._values.get("force_common_labels")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def ignore_missing_components(self) -> typing.Optional[builtins.bool]:
        '''IgnoreMissingComponents prevents kustomize from failing when components do not exist locally by not appending them to kustomization file.

        :schema: ApplicationSpecSourceKustomize#ignoreMissingComponents
        '''
        result = self._values.get("ignore_missing_components")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def images(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Images is a list of Kustomize image override specifications.

        :schema: ApplicationSpecSourceKustomize#images
        '''
        result = self._values.get("images")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def kube_version(self) -> typing.Optional[builtins.str]:
        '''KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests.

        By default, Argo CD
        uses the Kubernetes version of the target cluster.

        :schema: ApplicationSpecSourceKustomize#kubeVersion
        '''
        result = self._values.get("kube_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def label_include_templates(self) -> typing.Optional[builtins.bool]:
        '''LabelIncludeTemplates specifies whether to apply common labels to resource templates or not.

        :schema: ApplicationSpecSourceKustomize#labelIncludeTemplates
        '''
        result = self._values.get("label_include_templates")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def label_without_selector(self) -> typing.Optional[builtins.bool]:
        '''LabelWithoutSelector specifies whether to apply common labels to resource selectors or not.

        :schema: ApplicationSpecSourceKustomize#labelWithoutSelector
        '''
        result = self._values.get("label_without_selector")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def name_prefix(self) -> typing.Optional[builtins.str]:
        '''NamePrefix is a prefix appended to resources for Kustomize apps.

        :schema: ApplicationSpecSourceKustomize#namePrefix
        '''
        result = self._values.get("name_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace sets the namespace that Kustomize adds to all resources.

        :schema: ApplicationSpecSourceKustomize#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name_suffix(self) -> typing.Optional[builtins.str]:
        '''NameSuffix is a suffix appended to resources for Kustomize apps.

        :schema: ApplicationSpecSourceKustomize#nameSuffix
        '''
        result = self._values.get("name_suffix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def patches(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourceKustomizePatches"]]:
        '''Patches is a list of Kustomize patches.

        :schema: ApplicationSpecSourceKustomize#patches
        '''
        result = self._values.get("patches")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourceKustomizePatches"]], result)

    @builtins.property
    def replicas(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourceKustomizeReplicas"]]:
        '''Replicas is a list of Kustomize Replicas override specifications.

        :schema: ApplicationSpecSourceKustomize#replicas
        '''
        result = self._values.get("replicas")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourceKustomizeReplicas"]], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version controls which version of Kustomize to use for rendering manifests.

        :schema: ApplicationSpecSourceKustomize#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceKustomize(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceKustomizePatches",
    jsii_struct_bases=[],
    name_mapping={
        "options": "options",
        "patch": "patch",
        "path": "path",
        "target": "target",
    },
)
class ApplicationSpecSourceKustomizePatches:
    def __init__(
        self,
        *,
        options: typing.Optional[typing.Mapping[builtins.str, builtins.bool]] = None,
        patch: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        target: typing.Optional[typing.Union["ApplicationSpecSourceKustomizePatchesTarget", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param options: 
        :param patch: 
        :param path: 
        :param target: 

        :schema: ApplicationSpecSourceKustomizePatches
        '''
        if isinstance(target, dict):
            target = ApplicationSpecSourceKustomizePatchesTarget(**target)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__70b3e23903fafbd4c0887ff80abfab919b983639ed51c0f76a8c7a47a856c86b)
            check_type(argname="argument options", value=options, expected_type=type_hints["options"])
            check_type(argname="argument patch", value=patch, expected_type=type_hints["patch"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if options is not None:
            self._values["options"] = options
        if patch is not None:
            self._values["patch"] = patch
        if path is not None:
            self._values["path"] = path
        if target is not None:
            self._values["target"] = target

    @builtins.property
    def options(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.bool]]:
        '''
        :schema: ApplicationSpecSourceKustomizePatches#options
        '''
        result = self._values.get("options")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.bool]], result)

    @builtins.property
    def patch(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatches#patch
        '''
        result = self._values.get("patch")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatches#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target(self) -> typing.Optional["ApplicationSpecSourceKustomizePatchesTarget"]:
        '''
        :schema: ApplicationSpecSourceKustomizePatches#target
        '''
        result = self._values.get("target")
        return typing.cast(typing.Optional["ApplicationSpecSourceKustomizePatchesTarget"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceKustomizePatches(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceKustomizePatchesTarget",
    jsii_struct_bases=[],
    name_mapping={
        "annotation_selector": "annotationSelector",
        "group": "group",
        "kind": "kind",
        "label_selector": "labelSelector",
        "name": "name",
        "namespace": "namespace",
        "version": "version",
    },
)
class ApplicationSpecSourceKustomizePatchesTarget:
    def __init__(
        self,
        *,
        annotation_selector: typing.Optional[builtins.str] = None,
        group: typing.Optional[builtins.str] = None,
        kind: typing.Optional[builtins.str] = None,
        label_selector: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param annotation_selector: 
        :param group: 
        :param kind: 
        :param label_selector: 
        :param name: 
        :param namespace: 
        :param version: 

        :schema: ApplicationSpecSourceKustomizePatchesTarget
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b62415e715ebe025216d418440b87bae78b134fba99998197a8dffb31d81b80b)
            check_type(argname="argument annotation_selector", value=annotation_selector, expected_type=type_hints["annotation_selector"])
            check_type(argname="argument group", value=group, expected_type=type_hints["group"])
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument label_selector", value=label_selector, expected_type=type_hints["label_selector"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if annotation_selector is not None:
            self._values["annotation_selector"] = annotation_selector
        if group is not None:
            self._values["group"] = group
        if kind is not None:
            self._values["kind"] = kind
        if label_selector is not None:
            self._values["label_selector"] = label_selector
        if name is not None:
            self._values["name"] = name
        if namespace is not None:
            self._values["namespace"] = namespace
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def annotation_selector(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatchesTarget#annotationSelector
        '''
        result = self._values.get("annotation_selector")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def group(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatchesTarget#group
        '''
        result = self._values.get("group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def kind(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatchesTarget#kind
        '''
        result = self._values.get("kind")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def label_selector(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatchesTarget#labelSelector
        '''
        result = self._values.get("label_selector")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatchesTarget#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatchesTarget#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourceKustomizePatchesTarget#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceKustomizePatchesTarget(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourceKustomizeReplicas",
    jsii_struct_bases=[],
    name_mapping={"count": "count", "name": "name"},
)
class ApplicationSpecSourceKustomizeReplicas:
    def __init__(
        self,
        *,
        count: "ApplicationSpecSourceKustomizeReplicasCount",
        name: builtins.str,
    ) -> None:
        '''
        :param count: Number of replicas.
        :param name: Name of Deployment or StatefulSet.

        :schema: ApplicationSpecSourceKustomizeReplicas
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ced0c644f1f537b52c04c7db8bf6eef78afae7fbfeee7dc051ee2c2ce2ec950a)
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "count": count,
            "name": name,
        }

    @builtins.property
    def count(self) -> "ApplicationSpecSourceKustomizeReplicasCount":
        '''Number of replicas.

        :schema: ApplicationSpecSourceKustomizeReplicas#count
        '''
        result = self._values.get("count")
        assert result is not None, "Required property 'count' is missing"
        return typing.cast("ApplicationSpecSourceKustomizeReplicasCount", result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of Deployment or StatefulSet.

        :schema: ApplicationSpecSourceKustomizeReplicas#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourceKustomizeReplicas(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ApplicationSpecSourceKustomizeReplicasCount(
    metaclass=jsii.JSIIMeta,
    jsii_type="ioargoproj.ApplicationSpecSourceKustomizeReplicasCount",
):
    '''Number of replicas.

    :schema: ApplicationSpecSourceKustomizeReplicasCount
    '''

    @jsii.member(jsii_name="fromNumber")
    @builtins.classmethod
    def from_number(
        cls,
        value: jsii.Number,
    ) -> "ApplicationSpecSourceKustomizeReplicasCount":
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__00f1036b4458a51e88bb4c3f0c8943db31b96eea58341cd262de700602ee9302)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast("ApplicationSpecSourceKustomizeReplicasCount", jsii.sinvoke(cls, "fromNumber", [value]))

    @jsii.member(jsii_name="fromString")
    @builtins.classmethod
    def from_string(
        cls,
        value: builtins.str,
    ) -> "ApplicationSpecSourceKustomizeReplicasCount":
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d40c09d2e240a188b5984013a55672fb3d4cd562976a6abf94d26e9516d03669)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast("ApplicationSpecSourceKustomizeReplicasCount", jsii.sinvoke(cls, "fromString", [value]))

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(self) -> typing.Union[builtins.str, jsii.Number]:
        return typing.cast(typing.Union[builtins.str, jsii.Number], jsii.get(self, "value"))


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcePlugin",
    jsii_struct_bases=[],
    name_mapping={"env": "env", "name": "name", "parameters": "parameters"},
)
class ApplicationSpecSourcePlugin:
    def __init__(
        self,
        *,
        env: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcePluginEnv", typing.Dict[builtins.str, typing.Any]]]] = None,
        name: typing.Optional[builtins.str] = None,
        parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcePluginParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Plugin holds config management plugin specific options.

        :param env: Env is a list of environment variable entries.
        :param name: 
        :param parameters: 

        :schema: ApplicationSpecSourcePlugin
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__514024456f47697dcd1485e829ac7254241e1fc9c237d237549e6814f0ca49b2)
            check_type(argname="argument env", value=env, expected_type=type_hints["env"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if env is not None:
            self._values["env"] = env
        if name is not None:
            self._values["name"] = name
        if parameters is not None:
            self._values["parameters"] = parameters

    @builtins.property
    def env(self) -> typing.Optional[typing.List["ApplicationSpecSourcePluginEnv"]]:
        '''Env is a list of environment variable entries.

        :schema: ApplicationSpecSourcePlugin#env
        '''
        result = self._values.get("env")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcePluginEnv"]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcePlugin#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourcePluginParameters"]]:
        '''
        :schema: ApplicationSpecSourcePlugin#parameters
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcePluginParameters"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcePlugin(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcePluginEnv",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value"},
)
class ApplicationSpecSourcePluginEnv:
    def __init__(self, *, name: builtins.str, value: builtins.str) -> None:
        '''EnvEntry represents an entry in the application's environment.

        :param name: Name is the name of the variable, usually expressed in uppercase.
        :param value: Value is the value of the variable.

        :schema: ApplicationSpecSourcePluginEnv
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1ae2d9b6c9043f55f847eead5bf3a3fa62a6f74f130064c7bbefd9dbf44ec411)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''Name is the name of the variable, usually expressed in uppercase.

        :schema: ApplicationSpecSourcePluginEnv#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''Value is the value of the variable.

        :schema: ApplicationSpecSourcePluginEnv#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcePluginEnv(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcePluginParameters",
    jsii_struct_bases=[],
    name_mapping={"array": "array", "map": "map", "name": "name", "string": "string"},
)
class ApplicationSpecSourcePluginParameters:
    def __init__(
        self,
        *,
        array: typing.Optional[typing.Sequence[builtins.str]] = None,
        map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        string: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param array: Array is the value of an array type parameter.
        :param map: Map is the value of a map type parameter.
        :param name: Name is the name identifying a parameter.
        :param string: String_ is the value of a string type parameter.

        :schema: ApplicationSpecSourcePluginParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__67737a8e23a311401126a8ec69020232f8542fd2b263bea6431b759be0573142)
            check_type(argname="argument array", value=array, expected_type=type_hints["array"])
            check_type(argname="argument map", value=map, expected_type=type_hints["map"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument string", value=string, expected_type=type_hints["string"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if array is not None:
            self._values["array"] = array
        if map is not None:
            self._values["map"] = map
        if name is not None:
            self._values["name"] = name
        if string is not None:
            self._values["string"] = string

    @builtins.property
    def array(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array is the value of an array type parameter.

        :schema: ApplicationSpecSourcePluginParameters#array
        '''
        result = self._values.get("array")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def map(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Map is the value of a map type parameter.

        :schema: ApplicationSpecSourcePluginParameters#map
        '''
        result = self._values.get("map")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name identifying a parameter.

        :schema: ApplicationSpecSourcePluginParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def string(self) -> typing.Optional[builtins.str]:
        '''String_ is the value of a string type parameter.

        :schema: ApplicationSpecSourcePluginParameters#string
        '''
        result = self._values.get("string")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcePluginParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSources",
    jsii_struct_bases=[],
    name_mapping={
        "repo_url": "repoUrl",
        "chart": "chart",
        "directory": "directory",
        "helm": "helm",
        "kustomize": "kustomize",
        "name": "name",
        "path": "path",
        "plugin": "plugin",
        "ref": "ref",
        "target_revision": "targetRevision",
    },
)
class ApplicationSpecSources:
    def __init__(
        self,
        *,
        repo_url: builtins.str,
        chart: typing.Optional[builtins.str] = None,
        directory: typing.Optional[typing.Union["ApplicationSpecSourcesDirectory", typing.Dict[builtins.str, typing.Any]]] = None,
        helm: typing.Optional[typing.Union["ApplicationSpecSourcesHelm", typing.Dict[builtins.str, typing.Any]]] = None,
        kustomize: typing.Optional[typing.Union["ApplicationSpecSourcesKustomize", typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        plugin: typing.Optional[typing.Union["ApplicationSpecSourcesPlugin", typing.Dict[builtins.str, typing.Any]]] = None,
        ref: typing.Optional[builtins.str] = None,
        target_revision: typing.Optional[builtins.str] = None,
    ) -> None:
        '''ApplicationSource contains all required information about the source of an application.

        :param repo_url: RepoURL is the URL to the repository (Git or Helm) that contains the application manifests.
        :param chart: Chart is a Helm chart name, and must be specified for applications sourced from a Helm repo.
        :param directory: Directory holds path/directory specific options.
        :param helm: Helm holds helm specific options.
        :param kustomize: Kustomize holds kustomize specific options.
        :param name: Name is used to refer to a source and is displayed in the UI. It is used in multi-source Applications.
        :param path: Path is a directory path within the Git repository, and is only valid for applications sourced from Git.
        :param plugin: Plugin holds config management plugin specific options.
        :param ref: Ref is reference to another source within sources field. This field will not be used if used with a ``source`` tag.
        :param target_revision: TargetRevision defines the revision of the source to sync the application to. In case of Git, this can be commit, tag, or branch. If omitted, will equal to HEAD. In case of Helm, this is a semver tag for the Chart's version.

        :schema: ApplicationSpecSources
        '''
        if isinstance(directory, dict):
            directory = ApplicationSpecSourcesDirectory(**directory)
        if isinstance(helm, dict):
            helm = ApplicationSpecSourcesHelm(**helm)
        if isinstance(kustomize, dict):
            kustomize = ApplicationSpecSourcesKustomize(**kustomize)
        if isinstance(plugin, dict):
            plugin = ApplicationSpecSourcesPlugin(**plugin)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bc297ba23db9492421203bf6aed690cb8adc0c3321300e18c1e75b6c159fcc7c)
            check_type(argname="argument repo_url", value=repo_url, expected_type=type_hints["repo_url"])
            check_type(argname="argument chart", value=chart, expected_type=type_hints["chart"])
            check_type(argname="argument directory", value=directory, expected_type=type_hints["directory"])
            check_type(argname="argument helm", value=helm, expected_type=type_hints["helm"])
            check_type(argname="argument kustomize", value=kustomize, expected_type=type_hints["kustomize"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument plugin", value=plugin, expected_type=type_hints["plugin"])
            check_type(argname="argument ref", value=ref, expected_type=type_hints["ref"])
            check_type(argname="argument target_revision", value=target_revision, expected_type=type_hints["target_revision"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "repo_url": repo_url,
        }
        if chart is not None:
            self._values["chart"] = chart
        if directory is not None:
            self._values["directory"] = directory
        if helm is not None:
            self._values["helm"] = helm
        if kustomize is not None:
            self._values["kustomize"] = kustomize
        if name is not None:
            self._values["name"] = name
        if path is not None:
            self._values["path"] = path
        if plugin is not None:
            self._values["plugin"] = plugin
        if ref is not None:
            self._values["ref"] = ref
        if target_revision is not None:
            self._values["target_revision"] = target_revision

    @builtins.property
    def repo_url(self) -> builtins.str:
        '''RepoURL is the URL to the repository (Git or Helm) that contains the application manifests.

        :schema: ApplicationSpecSources#repoURL
        '''
        result = self._values.get("repo_url")
        assert result is not None, "Required property 'repo_url' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def chart(self) -> typing.Optional[builtins.str]:
        '''Chart is a Helm chart name, and must be specified for applications sourced from a Helm repo.

        :schema: ApplicationSpecSources#chart
        '''
        result = self._values.get("chart")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def directory(self) -> typing.Optional["ApplicationSpecSourcesDirectory"]:
        '''Directory holds path/directory specific options.

        :schema: ApplicationSpecSources#directory
        '''
        result = self._values.get("directory")
        return typing.cast(typing.Optional["ApplicationSpecSourcesDirectory"], result)

    @builtins.property
    def helm(self) -> typing.Optional["ApplicationSpecSourcesHelm"]:
        '''Helm holds helm specific options.

        :schema: ApplicationSpecSources#helm
        '''
        result = self._values.get("helm")
        return typing.cast(typing.Optional["ApplicationSpecSourcesHelm"], result)

    @builtins.property
    def kustomize(self) -> typing.Optional["ApplicationSpecSourcesKustomize"]:
        '''Kustomize holds kustomize specific options.

        :schema: ApplicationSpecSources#kustomize
        '''
        result = self._values.get("kustomize")
        return typing.cast(typing.Optional["ApplicationSpecSourcesKustomize"], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is used to refer to a source and is displayed in the UI.

        It is used in multi-source Applications.

        :schema: ApplicationSpecSources#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Path is a directory path within the Git repository, and is only valid for applications sourced from Git.

        :schema: ApplicationSpecSources#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def plugin(self) -> typing.Optional["ApplicationSpecSourcesPlugin"]:
        '''Plugin holds config management plugin specific options.

        :schema: ApplicationSpecSources#plugin
        '''
        result = self._values.get("plugin")
        return typing.cast(typing.Optional["ApplicationSpecSourcesPlugin"], result)

    @builtins.property
    def ref(self) -> typing.Optional[builtins.str]:
        '''Ref is reference to another source within sources field.

        This field will not be used if used with a ``source`` tag.

        :schema: ApplicationSpecSources#ref
        '''
        result = self._values.get("ref")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_revision(self) -> typing.Optional[builtins.str]:
        '''TargetRevision defines the revision of the source to sync the application to.

        In case of Git, this can be commit, tag, or branch. If omitted, will equal to HEAD.
        In case of Helm, this is a semver tag for the Chart's version.

        :schema: ApplicationSpecSources#targetRevision
        '''
        result = self._values.get("target_revision")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSources(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesDirectory",
    jsii_struct_bases=[],
    name_mapping={
        "exclude": "exclude",
        "include": "include",
        "jsonnet": "jsonnet",
        "recurse": "recurse",
    },
)
class ApplicationSpecSourcesDirectory:
    def __init__(
        self,
        *,
        exclude: typing.Optional[builtins.str] = None,
        include: typing.Optional[builtins.str] = None,
        jsonnet: typing.Optional[typing.Union["ApplicationSpecSourcesDirectoryJsonnet", typing.Dict[builtins.str, typing.Any]]] = None,
        recurse: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Directory holds path/directory specific options.

        :param exclude: Exclude contains a glob pattern to match paths against that should be explicitly excluded from being used during manifest generation.
        :param include: Include contains a glob pattern to match paths against that should be explicitly included during manifest generation.
        :param jsonnet: Jsonnet holds options specific to Jsonnet.
        :param recurse: Recurse specifies whether to scan a directory recursively for manifests.

        :schema: ApplicationSpecSourcesDirectory
        '''
        if isinstance(jsonnet, dict):
            jsonnet = ApplicationSpecSourcesDirectoryJsonnet(**jsonnet)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__378b764eb0eac08e33cdb65d1987cfbe7b054de9f12a072b3426e2bf51e5f9c0)
            check_type(argname="argument exclude", value=exclude, expected_type=type_hints["exclude"])
            check_type(argname="argument include", value=include, expected_type=type_hints["include"])
            check_type(argname="argument jsonnet", value=jsonnet, expected_type=type_hints["jsonnet"])
            check_type(argname="argument recurse", value=recurse, expected_type=type_hints["recurse"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if exclude is not None:
            self._values["exclude"] = exclude
        if include is not None:
            self._values["include"] = include
        if jsonnet is not None:
            self._values["jsonnet"] = jsonnet
        if recurse is not None:
            self._values["recurse"] = recurse

    @builtins.property
    def exclude(self) -> typing.Optional[builtins.str]:
        '''Exclude contains a glob pattern to match paths against that should be explicitly excluded from being used during manifest generation.

        :schema: ApplicationSpecSourcesDirectory#exclude
        '''
        result = self._values.get("exclude")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def include(self) -> typing.Optional[builtins.str]:
        '''Include contains a glob pattern to match paths against that should be explicitly included during manifest generation.

        :schema: ApplicationSpecSourcesDirectory#include
        '''
        result = self._values.get("include")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jsonnet(self) -> typing.Optional["ApplicationSpecSourcesDirectoryJsonnet"]:
        '''Jsonnet holds options specific to Jsonnet.

        :schema: ApplicationSpecSourcesDirectory#jsonnet
        '''
        result = self._values.get("jsonnet")
        return typing.cast(typing.Optional["ApplicationSpecSourcesDirectoryJsonnet"], result)

    @builtins.property
    def recurse(self) -> typing.Optional[builtins.bool]:
        '''Recurse specifies whether to scan a directory recursively for manifests.

        :schema: ApplicationSpecSourcesDirectory#recurse
        '''
        result = self._values.get("recurse")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesDirectory(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesDirectoryJsonnet",
    jsii_struct_bases=[],
    name_mapping={"ext_vars": "extVars", "libs": "libs", "tlas": "tlas"},
)
class ApplicationSpecSourcesDirectoryJsonnet:
    def __init__(
        self,
        *,
        ext_vars: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcesDirectoryJsonnetExtVars", typing.Dict[builtins.str, typing.Any]]]] = None,
        libs: typing.Optional[typing.Sequence[builtins.str]] = None,
        tlas: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcesDirectoryJsonnetTlas", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Jsonnet holds options specific to Jsonnet.

        :param ext_vars: ExtVars is a list of Jsonnet External Variables.
        :param libs: Additional library search dirs.
        :param tlas: TLAS is a list of Jsonnet Top-level Arguments.

        :schema: ApplicationSpecSourcesDirectoryJsonnet
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c7d77b294df6b010096428e2c6294e171281911fbfae7aca5359c43f32bc0461)
            check_type(argname="argument ext_vars", value=ext_vars, expected_type=type_hints["ext_vars"])
            check_type(argname="argument libs", value=libs, expected_type=type_hints["libs"])
            check_type(argname="argument tlas", value=tlas, expected_type=type_hints["tlas"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if ext_vars is not None:
            self._values["ext_vars"] = ext_vars
        if libs is not None:
            self._values["libs"] = libs
        if tlas is not None:
            self._values["tlas"] = tlas

    @builtins.property
    def ext_vars(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourcesDirectoryJsonnetExtVars"]]:
        '''ExtVars is a list of Jsonnet External Variables.

        :schema: ApplicationSpecSourcesDirectoryJsonnet#extVars
        '''
        result = self._values.get("ext_vars")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcesDirectoryJsonnetExtVars"]], result)

    @builtins.property
    def libs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Additional library search dirs.

        :schema: ApplicationSpecSourcesDirectoryJsonnet#libs
        '''
        result = self._values.get("libs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def tlas(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourcesDirectoryJsonnetTlas"]]:
        '''TLAS is a list of Jsonnet Top-level Arguments.

        :schema: ApplicationSpecSourcesDirectoryJsonnet#tlas
        '''
        result = self._values.get("tlas")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcesDirectoryJsonnetTlas"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesDirectoryJsonnet(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesDirectoryJsonnetExtVars",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value", "code": "code"},
)
class ApplicationSpecSourcesDirectoryJsonnetExtVars:
    def __init__(
        self,
        *,
        name: builtins.str,
        value: builtins.str,
        code: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''JsonnetVar represents a variable to be passed to jsonnet during manifest generation.

        :param name: 
        :param value: 
        :param code: 

        :schema: ApplicationSpecSourcesDirectoryJsonnetExtVars
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__845dd159a281f4bf8d3ea96f5ae116bc3e010f1ed417747aab930c910555613c)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument code", value=code, expected_type=type_hints["code"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }
        if code is not None:
            self._values["code"] = code

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationSpecSourcesDirectoryJsonnetExtVars#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationSpecSourcesDirectoryJsonnetExtVars#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def code(self) -> typing.Optional[builtins.bool]:
        '''
        :schema: ApplicationSpecSourcesDirectoryJsonnetExtVars#code
        '''
        result = self._values.get("code")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesDirectoryJsonnetExtVars(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesDirectoryJsonnetTlas",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value", "code": "code"},
)
class ApplicationSpecSourcesDirectoryJsonnetTlas:
    def __init__(
        self,
        *,
        name: builtins.str,
        value: builtins.str,
        code: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''JsonnetVar represents a variable to be passed to jsonnet during manifest generation.

        :param name: 
        :param value: 
        :param code: 

        :schema: ApplicationSpecSourcesDirectoryJsonnetTlas
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a2c5c54f2e2f92a477a591ee6b87292e5000ea574fb8b3ea0864194d159d0ee6)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument code", value=code, expected_type=type_hints["code"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }
        if code is not None:
            self._values["code"] = code

    @builtins.property
    def name(self) -> builtins.str:
        '''
        :schema: ApplicationSpecSourcesDirectoryJsonnetTlas#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''
        :schema: ApplicationSpecSourcesDirectoryJsonnetTlas#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def code(self) -> typing.Optional[builtins.bool]:
        '''
        :schema: ApplicationSpecSourcesDirectoryJsonnetTlas#code
        '''
        result = self._values.get("code")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesDirectoryJsonnetTlas(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesHelm",
    jsii_struct_bases=[],
    name_mapping={
        "api_versions": "apiVersions",
        "file_parameters": "fileParameters",
        "ignore_missing_value_files": "ignoreMissingValueFiles",
        "kube_version": "kubeVersion",
        "namespace": "namespace",
        "parameters": "parameters",
        "pass_credentials": "passCredentials",
        "release_name": "releaseName",
        "skip_crds": "skipCrds",
        "skip_schema_validation": "skipSchemaValidation",
        "skip_tests": "skipTests",
        "value_files": "valueFiles",
        "values": "values",
        "values_object": "valuesObject",
        "version": "version",
    },
)
class ApplicationSpecSourcesHelm:
    def __init__(
        self,
        *,
        api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
        file_parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcesHelmFileParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_missing_value_files: typing.Optional[builtins.bool] = None,
        kube_version: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcesHelmParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
        pass_credentials: typing.Optional[builtins.bool] = None,
        release_name: typing.Optional[builtins.str] = None,
        skip_crds: typing.Optional[builtins.bool] = None,
        skip_schema_validation: typing.Optional[builtins.bool] = None,
        skip_tests: typing.Optional[builtins.bool] = None,
        value_files: typing.Optional[typing.Sequence[builtins.str]] = None,
        values: typing.Optional[builtins.str] = None,
        values_object: typing.Any = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Helm holds helm specific options.

        :param api_versions: APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests. By default, Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.
        :param file_parameters: FileParameters are file parameters to the helm template.
        :param ignore_missing_value_files: IgnoreMissingValueFiles prevents helm template from failing when valueFiles do not exist locally by not appending them to helm template --values.
        :param kube_version: KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests. By default, Argo CD uses the Kubernetes version of the target cluster.
        :param namespace: Namespace is an optional namespace to template with. If left empty, defaults to the app's destination namespace.
        :param parameters: Parameters is a list of Helm parameters which are passed to the helm template command upon manifest generation.
        :param pass_credentials: PassCredentials pass credentials to all domains (Helm's --pass-credentials).
        :param release_name: ReleaseName is the Helm release name to use. If omitted it will use the application name
        :param skip_crds: SkipCrds skips custom resource definition installation step (Helm's --skip-crds).
        :param skip_schema_validation: SkipSchemaValidation skips JSON schema validation (Helm's --skip-schema-validation).
        :param skip_tests: SkipTests skips test manifest installation step (Helm's --skip-tests).
        :param value_files: ValuesFiles is a list of Helm value files to use when generating a template.
        :param values: Values specifies Helm values to be passed to helm template, typically defined as a block. ValuesObject takes precedence over Values, so use one or the other.
        :param values_object: ValuesObject specifies Helm values to be passed to helm template, defined as a map. This takes precedence over Values.
        :param version: Version is the Helm version to use for templating ("3").

        :schema: ApplicationSpecSourcesHelm
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__31ab5c861d3f1bd80908a8acea70c092f42f8da0189b0888973af0bdacfa163d)
            check_type(argname="argument api_versions", value=api_versions, expected_type=type_hints["api_versions"])
            check_type(argname="argument file_parameters", value=file_parameters, expected_type=type_hints["file_parameters"])
            check_type(argname="argument ignore_missing_value_files", value=ignore_missing_value_files, expected_type=type_hints["ignore_missing_value_files"])
            check_type(argname="argument kube_version", value=kube_version, expected_type=type_hints["kube_version"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
            check_type(argname="argument pass_credentials", value=pass_credentials, expected_type=type_hints["pass_credentials"])
            check_type(argname="argument release_name", value=release_name, expected_type=type_hints["release_name"])
            check_type(argname="argument skip_crds", value=skip_crds, expected_type=type_hints["skip_crds"])
            check_type(argname="argument skip_schema_validation", value=skip_schema_validation, expected_type=type_hints["skip_schema_validation"])
            check_type(argname="argument skip_tests", value=skip_tests, expected_type=type_hints["skip_tests"])
            check_type(argname="argument value_files", value=value_files, expected_type=type_hints["value_files"])
            check_type(argname="argument values", value=values, expected_type=type_hints["values"])
            check_type(argname="argument values_object", value=values_object, expected_type=type_hints["values_object"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_versions is not None:
            self._values["api_versions"] = api_versions
        if file_parameters is not None:
            self._values["file_parameters"] = file_parameters
        if ignore_missing_value_files is not None:
            self._values["ignore_missing_value_files"] = ignore_missing_value_files
        if kube_version is not None:
            self._values["kube_version"] = kube_version
        if namespace is not None:
            self._values["namespace"] = namespace
        if parameters is not None:
            self._values["parameters"] = parameters
        if pass_credentials is not None:
            self._values["pass_credentials"] = pass_credentials
        if release_name is not None:
            self._values["release_name"] = release_name
        if skip_crds is not None:
            self._values["skip_crds"] = skip_crds
        if skip_schema_validation is not None:
            self._values["skip_schema_validation"] = skip_schema_validation
        if skip_tests is not None:
            self._values["skip_tests"] = skip_tests
        if value_files is not None:
            self._values["value_files"] = value_files
        if values is not None:
            self._values["values"] = values
        if values_object is not None:
            self._values["values_object"] = values_object
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def api_versions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests.

        By default,
        Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.

        :schema: ApplicationSpecSourcesHelm#apiVersions
        '''
        result = self._values.get("api_versions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def file_parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourcesHelmFileParameters"]]:
        '''FileParameters are file parameters to the helm template.

        :schema: ApplicationSpecSourcesHelm#fileParameters
        '''
        result = self._values.get("file_parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcesHelmFileParameters"]], result)

    @builtins.property
    def ignore_missing_value_files(self) -> typing.Optional[builtins.bool]:
        '''IgnoreMissingValueFiles prevents helm template from failing when valueFiles do not exist locally by not appending them to helm template --values.

        :schema: ApplicationSpecSourcesHelm#ignoreMissingValueFiles
        '''
        result = self._values.get("ignore_missing_value_files")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def kube_version(self) -> typing.Optional[builtins.str]:
        '''KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests.

        By default, Argo CD
        uses the Kubernetes version of the target cluster.

        :schema: ApplicationSpecSourcesHelm#kubeVersion
        '''
        result = self._values.get("kube_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace is an optional namespace to template with.

        If left empty, defaults to the app's destination namespace.

        :schema: ApplicationSpecSourcesHelm#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourcesHelmParameters"]]:
        '''Parameters is a list of Helm parameters which are passed to the helm template command upon manifest generation.

        :schema: ApplicationSpecSourcesHelm#parameters
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcesHelmParameters"]], result)

    @builtins.property
    def pass_credentials(self) -> typing.Optional[builtins.bool]:
        '''PassCredentials pass credentials to all domains (Helm's --pass-credentials).

        :schema: ApplicationSpecSourcesHelm#passCredentials
        '''
        result = self._values.get("pass_credentials")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_name(self) -> typing.Optional[builtins.str]:
        '''ReleaseName is the Helm release name to use.

        If omitted it will use the application name

        :schema: ApplicationSpecSourcesHelm#releaseName
        '''
        result = self._values.get("release_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def skip_crds(self) -> typing.Optional[builtins.bool]:
        '''SkipCrds skips custom resource definition installation step (Helm's --skip-crds).

        :schema: ApplicationSpecSourcesHelm#skipCrds
        '''
        result = self._values.get("skip_crds")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip_schema_validation(self) -> typing.Optional[builtins.bool]:
        '''SkipSchemaValidation skips JSON schema validation (Helm's --skip-schema-validation).

        :schema: ApplicationSpecSourcesHelm#skipSchemaValidation
        '''
        result = self._values.get("skip_schema_validation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def skip_tests(self) -> typing.Optional[builtins.bool]:
        '''SkipTests skips test manifest installation step (Helm's --skip-tests).

        :schema: ApplicationSpecSourcesHelm#skipTests
        '''
        result = self._values.get("skip_tests")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def value_files(self) -> typing.Optional[typing.List[builtins.str]]:
        '''ValuesFiles is a list of Helm value files to use when generating a template.

        :schema: ApplicationSpecSourcesHelm#valueFiles
        '''
        result = self._values.get("value_files")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def values(self) -> typing.Optional[builtins.str]:
        '''Values specifies Helm values to be passed to helm template, typically defined as a block.

        ValuesObject takes precedence over Values, so use one or the other.

        :schema: ApplicationSpecSourcesHelm#values
        '''
        result = self._values.get("values")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def values_object(self) -> typing.Any:
        '''ValuesObject specifies Helm values to be passed to helm template, defined as a map.

        This takes precedence over Values.

        :schema: ApplicationSpecSourcesHelm#valuesObject
        '''
        result = self._values.get("values_object")
        return typing.cast(typing.Any, result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version is the Helm version to use for templating ("3").

        :schema: ApplicationSpecSourcesHelm#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesHelm(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesHelmFileParameters",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "path": "path"},
)
class ApplicationSpecSourcesHelmFileParameters:
    def __init__(
        self,
        *,
        name: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HelmFileParameter is a file parameter that's passed to helm template during manifest generation.

        :param name: Name is the name of the Helm parameter.
        :param path: Path is the path to the file containing the values for the Helm parameter.

        :schema: ApplicationSpecSourcesHelmFileParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3591c6b32ad894aa4b81618948d9d1e77dbf3cc1cb1de9eff3b9c92ce2dc199d)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if name is not None:
            self._values["name"] = name
        if path is not None:
            self._values["path"] = path

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name of the Helm parameter.

        :schema: ApplicationSpecSourcesHelmFileParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''Path is the path to the file containing the values for the Helm parameter.

        :schema: ApplicationSpecSourcesHelmFileParameters#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesHelmFileParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesHelmParameters",
    jsii_struct_bases=[],
    name_mapping={"force_string": "forceString", "name": "name", "value": "value"},
)
class ApplicationSpecSourcesHelmParameters:
    def __init__(
        self,
        *,
        force_string: typing.Optional[builtins.bool] = None,
        name: typing.Optional[builtins.str] = None,
        value: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HelmParameter is a parameter that's passed to helm template during manifest generation.

        :param force_string: ForceString determines whether to tell Helm to interpret booleans and numbers as strings.
        :param name: Name is the name of the Helm parameter.
        :param value: Value is the value for the Helm parameter.

        :schema: ApplicationSpecSourcesHelmParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a9024cde9c2ff5ca9b5f536937ed4dc212d6b6100b40e97306fd954dfaddf6c2)
            check_type(argname="argument force_string", value=force_string, expected_type=type_hints["force_string"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if force_string is not None:
            self._values["force_string"] = force_string
        if name is not None:
            self._values["name"] = name
        if value is not None:
            self._values["value"] = value

    @builtins.property
    def force_string(self) -> typing.Optional[builtins.bool]:
        '''ForceString determines whether to tell Helm to interpret booleans and numbers as strings.

        :schema: ApplicationSpecSourcesHelmParameters#forceString
        '''
        result = self._values.get("force_string")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name of the Helm parameter.

        :schema: ApplicationSpecSourcesHelmParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def value(self) -> typing.Optional[builtins.str]:
        '''Value is the value for the Helm parameter.

        :schema: ApplicationSpecSourcesHelmParameters#value
        '''
        result = self._values.get("value")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesHelmParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesKustomize",
    jsii_struct_bases=[],
    name_mapping={
        "api_versions": "apiVersions",
        "common_annotations": "commonAnnotations",
        "common_annotations_envsubst": "commonAnnotationsEnvsubst",
        "common_labels": "commonLabels",
        "components": "components",
        "force_common_annotations": "forceCommonAnnotations",
        "force_common_labels": "forceCommonLabels",
        "ignore_missing_components": "ignoreMissingComponents",
        "images": "images",
        "kube_version": "kubeVersion",
        "label_include_templates": "labelIncludeTemplates",
        "label_without_selector": "labelWithoutSelector",
        "name_prefix": "namePrefix",
        "namespace": "namespace",
        "name_suffix": "nameSuffix",
        "patches": "patches",
        "replicas": "replicas",
        "version": "version",
    },
)
class ApplicationSpecSourcesKustomize:
    def __init__(
        self,
        *,
        api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
        common_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        common_annotations_envsubst: typing.Optional[builtins.bool] = None,
        common_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        components: typing.Optional[typing.Sequence[builtins.str]] = None,
        force_common_annotations: typing.Optional[builtins.bool] = None,
        force_common_labels: typing.Optional[builtins.bool] = None,
        ignore_missing_components: typing.Optional[builtins.bool] = None,
        images: typing.Optional[typing.Sequence[builtins.str]] = None,
        kube_version: typing.Optional[builtins.str] = None,
        label_include_templates: typing.Optional[builtins.bool] = None,
        label_without_selector: typing.Optional[builtins.bool] = None,
        name_prefix: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        name_suffix: typing.Optional[builtins.str] = None,
        patches: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcesKustomizePatches", typing.Dict[builtins.str, typing.Any]]]] = None,
        replicas: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcesKustomizeReplicas", typing.Dict[builtins.str, typing.Any]]]] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Kustomize holds kustomize specific options.

        :param api_versions: APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests. By default, Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.
        :param common_annotations: CommonAnnotations is a list of additional annotations to add to rendered manifests.
        :param common_annotations_envsubst: CommonAnnotationsEnvsubst specifies whether to apply env variables substitution for annotation values.
        :param common_labels: CommonLabels is a list of additional labels to add to rendered manifests.
        :param components: Components specifies a list of kustomize components to add to the kustomization before building.
        :param force_common_annotations: ForceCommonAnnotations specifies whether to force applying common annotations to resources for Kustomize apps.
        :param force_common_labels: ForceCommonLabels specifies whether to force applying common labels to resources for Kustomize apps.
        :param ignore_missing_components: IgnoreMissingComponents prevents kustomize from failing when components do not exist locally by not appending them to kustomization file.
        :param images: Images is a list of Kustomize image override specifications.
        :param kube_version: KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests. By default, Argo CD uses the Kubernetes version of the target cluster.
        :param label_include_templates: LabelIncludeTemplates specifies whether to apply common labels to resource templates or not.
        :param label_without_selector: LabelWithoutSelector specifies whether to apply common labels to resource selectors or not.
        :param name_prefix: NamePrefix is a prefix appended to resources for Kustomize apps.
        :param namespace: Namespace sets the namespace that Kustomize adds to all resources.
        :param name_suffix: NameSuffix is a suffix appended to resources for Kustomize apps.
        :param patches: Patches is a list of Kustomize patches.
        :param replicas: Replicas is a list of Kustomize Replicas override specifications.
        :param version: Version controls which version of Kustomize to use for rendering manifests.

        :schema: ApplicationSpecSourcesKustomize
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0ac1b1f59ae49a9d56c4cfacc0c940b516a5e8081676741e72b08c59feb6c0f5)
            check_type(argname="argument api_versions", value=api_versions, expected_type=type_hints["api_versions"])
            check_type(argname="argument common_annotations", value=common_annotations, expected_type=type_hints["common_annotations"])
            check_type(argname="argument common_annotations_envsubst", value=common_annotations_envsubst, expected_type=type_hints["common_annotations_envsubst"])
            check_type(argname="argument common_labels", value=common_labels, expected_type=type_hints["common_labels"])
            check_type(argname="argument components", value=components, expected_type=type_hints["components"])
            check_type(argname="argument force_common_annotations", value=force_common_annotations, expected_type=type_hints["force_common_annotations"])
            check_type(argname="argument force_common_labels", value=force_common_labels, expected_type=type_hints["force_common_labels"])
            check_type(argname="argument ignore_missing_components", value=ignore_missing_components, expected_type=type_hints["ignore_missing_components"])
            check_type(argname="argument images", value=images, expected_type=type_hints["images"])
            check_type(argname="argument kube_version", value=kube_version, expected_type=type_hints["kube_version"])
            check_type(argname="argument label_include_templates", value=label_include_templates, expected_type=type_hints["label_include_templates"])
            check_type(argname="argument label_without_selector", value=label_without_selector, expected_type=type_hints["label_without_selector"])
            check_type(argname="argument name_prefix", value=name_prefix, expected_type=type_hints["name_prefix"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument name_suffix", value=name_suffix, expected_type=type_hints["name_suffix"])
            check_type(argname="argument patches", value=patches, expected_type=type_hints["patches"])
            check_type(argname="argument replicas", value=replicas, expected_type=type_hints["replicas"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_versions is not None:
            self._values["api_versions"] = api_versions
        if common_annotations is not None:
            self._values["common_annotations"] = common_annotations
        if common_annotations_envsubst is not None:
            self._values["common_annotations_envsubst"] = common_annotations_envsubst
        if common_labels is not None:
            self._values["common_labels"] = common_labels
        if components is not None:
            self._values["components"] = components
        if force_common_annotations is not None:
            self._values["force_common_annotations"] = force_common_annotations
        if force_common_labels is not None:
            self._values["force_common_labels"] = force_common_labels
        if ignore_missing_components is not None:
            self._values["ignore_missing_components"] = ignore_missing_components
        if images is not None:
            self._values["images"] = images
        if kube_version is not None:
            self._values["kube_version"] = kube_version
        if label_include_templates is not None:
            self._values["label_include_templates"] = label_include_templates
        if label_without_selector is not None:
            self._values["label_without_selector"] = label_without_selector
        if name_prefix is not None:
            self._values["name_prefix"] = name_prefix
        if namespace is not None:
            self._values["namespace"] = namespace
        if name_suffix is not None:
            self._values["name_suffix"] = name_suffix
        if patches is not None:
            self._values["patches"] = patches
        if replicas is not None:
            self._values["replicas"] = replicas
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def api_versions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''APIVersions specifies the Kubernetes resource API versions to pass to Helm when templating manifests.

        By default,
        Argo CD uses the API versions of the target cluster. The format is [group/]version/kind.

        :schema: ApplicationSpecSourcesKustomize#apiVersions
        '''
        result = self._values.get("api_versions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def common_annotations(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''CommonAnnotations is a list of additional annotations to add to rendered manifests.

        :schema: ApplicationSpecSourcesKustomize#commonAnnotations
        '''
        result = self._values.get("common_annotations")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def common_annotations_envsubst(self) -> typing.Optional[builtins.bool]:
        '''CommonAnnotationsEnvsubst specifies whether to apply env variables substitution for annotation values.

        :schema: ApplicationSpecSourcesKustomize#commonAnnotationsEnvsubst
        '''
        result = self._values.get("common_annotations_envsubst")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def common_labels(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''CommonLabels is a list of additional labels to add to rendered manifests.

        :schema: ApplicationSpecSourcesKustomize#commonLabels
        '''
        result = self._values.get("common_labels")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def components(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Components specifies a list of kustomize components to add to the kustomization before building.

        :schema: ApplicationSpecSourcesKustomize#components
        '''
        result = self._values.get("components")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def force_common_annotations(self) -> typing.Optional[builtins.bool]:
        '''ForceCommonAnnotations specifies whether to force applying common annotations to resources for Kustomize apps.

        :schema: ApplicationSpecSourcesKustomize#forceCommonAnnotations
        '''
        result = self._values.get("force_common_annotations")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def force_common_labels(self) -> typing.Optional[builtins.bool]:
        '''ForceCommonLabels specifies whether to force applying common labels to resources for Kustomize apps.

        :schema: ApplicationSpecSourcesKustomize#forceCommonLabels
        '''
        result = self._values.get("force_common_labels")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def ignore_missing_components(self) -> typing.Optional[builtins.bool]:
        '''IgnoreMissingComponents prevents kustomize from failing when components do not exist locally by not appending them to kustomization file.

        :schema: ApplicationSpecSourcesKustomize#ignoreMissingComponents
        '''
        result = self._values.get("ignore_missing_components")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def images(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Images is a list of Kustomize image override specifications.

        :schema: ApplicationSpecSourcesKustomize#images
        '''
        result = self._values.get("images")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def kube_version(self) -> typing.Optional[builtins.str]:
        '''KubeVersion specifies the Kubernetes API version to pass to Helm when templating manifests.

        By default, Argo CD
        uses the Kubernetes version of the target cluster.

        :schema: ApplicationSpecSourcesKustomize#kubeVersion
        '''
        result = self._values.get("kube_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def label_include_templates(self) -> typing.Optional[builtins.bool]:
        '''LabelIncludeTemplates specifies whether to apply common labels to resource templates or not.

        :schema: ApplicationSpecSourcesKustomize#labelIncludeTemplates
        '''
        result = self._values.get("label_include_templates")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def label_without_selector(self) -> typing.Optional[builtins.bool]:
        '''LabelWithoutSelector specifies whether to apply common labels to resource selectors or not.

        :schema: ApplicationSpecSourcesKustomize#labelWithoutSelector
        '''
        result = self._values.get("label_without_selector")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def name_prefix(self) -> typing.Optional[builtins.str]:
        '''NamePrefix is a prefix appended to resources for Kustomize apps.

        :schema: ApplicationSpecSourcesKustomize#namePrefix
        '''
        result = self._values.get("name_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''Namespace sets the namespace that Kustomize adds to all resources.

        :schema: ApplicationSpecSourcesKustomize#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name_suffix(self) -> typing.Optional[builtins.str]:
        '''NameSuffix is a suffix appended to resources for Kustomize apps.

        :schema: ApplicationSpecSourcesKustomize#nameSuffix
        '''
        result = self._values.get("name_suffix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def patches(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourcesKustomizePatches"]]:
        '''Patches is a list of Kustomize patches.

        :schema: ApplicationSpecSourcesKustomize#patches
        '''
        result = self._values.get("patches")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcesKustomizePatches"]], result)

    @builtins.property
    def replicas(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourcesKustomizeReplicas"]]:
        '''Replicas is a list of Kustomize Replicas override specifications.

        :schema: ApplicationSpecSourcesKustomize#replicas
        '''
        result = self._values.get("replicas")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcesKustomizeReplicas"]], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version controls which version of Kustomize to use for rendering manifests.

        :schema: ApplicationSpecSourcesKustomize#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesKustomize(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesKustomizePatches",
    jsii_struct_bases=[],
    name_mapping={
        "options": "options",
        "patch": "patch",
        "path": "path",
        "target": "target",
    },
)
class ApplicationSpecSourcesKustomizePatches:
    def __init__(
        self,
        *,
        options: typing.Optional[typing.Mapping[builtins.str, builtins.bool]] = None,
        patch: typing.Optional[builtins.str] = None,
        path: typing.Optional[builtins.str] = None,
        target: typing.Optional[typing.Union["ApplicationSpecSourcesKustomizePatchesTarget", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param options: 
        :param patch: 
        :param path: 
        :param target: 

        :schema: ApplicationSpecSourcesKustomizePatches
        '''
        if isinstance(target, dict):
            target = ApplicationSpecSourcesKustomizePatchesTarget(**target)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ffa8c76ef3ae39471dde2a8af16df254b34a7f5069f06dc2fd59980ee4d89048)
            check_type(argname="argument options", value=options, expected_type=type_hints["options"])
            check_type(argname="argument patch", value=patch, expected_type=type_hints["patch"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if options is not None:
            self._values["options"] = options
        if patch is not None:
            self._values["patch"] = patch
        if path is not None:
            self._values["path"] = path
        if target is not None:
            self._values["target"] = target

    @builtins.property
    def options(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.bool]]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatches#options
        '''
        result = self._values.get("options")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.bool]], result)

    @builtins.property
    def patch(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatches#patch
        '''
        result = self._values.get("patch")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def path(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatches#path
        '''
        result = self._values.get("path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target(self) -> typing.Optional["ApplicationSpecSourcesKustomizePatchesTarget"]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatches#target
        '''
        result = self._values.get("target")
        return typing.cast(typing.Optional["ApplicationSpecSourcesKustomizePatchesTarget"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesKustomizePatches(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesKustomizePatchesTarget",
    jsii_struct_bases=[],
    name_mapping={
        "annotation_selector": "annotationSelector",
        "group": "group",
        "kind": "kind",
        "label_selector": "labelSelector",
        "name": "name",
        "namespace": "namespace",
        "version": "version",
    },
)
class ApplicationSpecSourcesKustomizePatchesTarget:
    def __init__(
        self,
        *,
        annotation_selector: typing.Optional[builtins.str] = None,
        group: typing.Optional[builtins.str] = None,
        kind: typing.Optional[builtins.str] = None,
        label_selector: typing.Optional[builtins.str] = None,
        name: typing.Optional[builtins.str] = None,
        namespace: typing.Optional[builtins.str] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param annotation_selector: 
        :param group: 
        :param kind: 
        :param label_selector: 
        :param name: 
        :param namespace: 
        :param version: 

        :schema: ApplicationSpecSourcesKustomizePatchesTarget
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5869f465abbf268cc52d050c076351daae4e722d61fdeef9584c9c55514d687d)
            check_type(argname="argument annotation_selector", value=annotation_selector, expected_type=type_hints["annotation_selector"])
            check_type(argname="argument group", value=group, expected_type=type_hints["group"])
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument label_selector", value=label_selector, expected_type=type_hints["label_selector"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if annotation_selector is not None:
            self._values["annotation_selector"] = annotation_selector
        if group is not None:
            self._values["group"] = group
        if kind is not None:
            self._values["kind"] = kind
        if label_selector is not None:
            self._values["label_selector"] = label_selector
        if name is not None:
            self._values["name"] = name
        if namespace is not None:
            self._values["namespace"] = namespace
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def annotation_selector(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatchesTarget#annotationSelector
        '''
        result = self._values.get("annotation_selector")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def group(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatchesTarget#group
        '''
        result = self._values.get("group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def kind(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatchesTarget#kind
        '''
        result = self._values.get("kind")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def label_selector(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatchesTarget#labelSelector
        '''
        result = self._values.get("label_selector")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatchesTarget#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatchesTarget#namespace
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesKustomizePatchesTarget#version
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesKustomizePatchesTarget(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesKustomizeReplicas",
    jsii_struct_bases=[],
    name_mapping={"count": "count", "name": "name"},
)
class ApplicationSpecSourcesKustomizeReplicas:
    def __init__(
        self,
        *,
        count: "ApplicationSpecSourcesKustomizeReplicasCount",
        name: builtins.str,
    ) -> None:
        '''
        :param count: Number of replicas.
        :param name: Name of Deployment or StatefulSet.

        :schema: ApplicationSpecSourcesKustomizeReplicas
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a9b8a1ae0df6140ebcd9dbe74b71d52f20ebfbae415fa412b8ee093bdc6f8b52)
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "count": count,
            "name": name,
        }

    @builtins.property
    def count(self) -> "ApplicationSpecSourcesKustomizeReplicasCount":
        '''Number of replicas.

        :schema: ApplicationSpecSourcesKustomizeReplicas#count
        '''
        result = self._values.get("count")
        assert result is not None, "Required property 'count' is missing"
        return typing.cast("ApplicationSpecSourcesKustomizeReplicasCount", result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of Deployment or StatefulSet.

        :schema: ApplicationSpecSourcesKustomizeReplicas#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesKustomizeReplicas(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ApplicationSpecSourcesKustomizeReplicasCount(
    metaclass=jsii.JSIIMeta,
    jsii_type="ioargoproj.ApplicationSpecSourcesKustomizeReplicasCount",
):
    '''Number of replicas.

    :schema: ApplicationSpecSourcesKustomizeReplicasCount
    '''

    @jsii.member(jsii_name="fromNumber")
    @builtins.classmethod
    def from_number(
        cls,
        value: jsii.Number,
    ) -> "ApplicationSpecSourcesKustomizeReplicasCount":
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b3049c79710732ba890aabc204a39455b860b0661ca354f765f2ab4c0286d4aa)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast("ApplicationSpecSourcesKustomizeReplicasCount", jsii.sinvoke(cls, "fromNumber", [value]))

    @jsii.member(jsii_name="fromString")
    @builtins.classmethod
    def from_string(
        cls,
        value: builtins.str,
    ) -> "ApplicationSpecSourcesKustomizeReplicasCount":
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__076d3e9a255054ef7b8b9de93f5f3f5bf95d4c1925ca7269ae7cdb08bb33ec77)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast("ApplicationSpecSourcesKustomizeReplicasCount", jsii.sinvoke(cls, "fromString", [value]))

    @builtins.property
    @jsii.member(jsii_name="value")
    def value(self) -> typing.Union[builtins.str, jsii.Number]:
        return typing.cast(typing.Union[builtins.str, jsii.Number], jsii.get(self, "value"))


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesPlugin",
    jsii_struct_bases=[],
    name_mapping={"env": "env", "name": "name", "parameters": "parameters"},
)
class ApplicationSpecSourcesPlugin:
    def __init__(
        self,
        *,
        env: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcesPluginEnv", typing.Dict[builtins.str, typing.Any]]]] = None,
        name: typing.Optional[builtins.str] = None,
        parameters: typing.Optional[typing.Sequence[typing.Union["ApplicationSpecSourcesPluginParameters", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Plugin holds config management plugin specific options.

        :param env: Env is a list of environment variable entries.
        :param name: 
        :param parameters: 

        :schema: ApplicationSpecSourcesPlugin
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__89df259930d4320290e71fd7d731a9ceb29ffe1e62151cc3172d6419e96e0787)
            check_type(argname="argument env", value=env, expected_type=type_hints["env"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if env is not None:
            self._values["env"] = env
        if name is not None:
            self._values["name"] = name
        if parameters is not None:
            self._values["parameters"] = parameters

    @builtins.property
    def env(self) -> typing.Optional[typing.List["ApplicationSpecSourcesPluginEnv"]]:
        '''Env is a list of environment variable entries.

        :schema: ApplicationSpecSourcesPlugin#env
        '''
        result = self._values.get("env")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcesPluginEnv"]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''
        :schema: ApplicationSpecSourcesPlugin#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(
        self,
    ) -> typing.Optional[typing.List["ApplicationSpecSourcesPluginParameters"]]:
        '''
        :schema: ApplicationSpecSourcesPlugin#parameters
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Optional[typing.List["ApplicationSpecSourcesPluginParameters"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesPlugin(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesPluginEnv",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "value": "value"},
)
class ApplicationSpecSourcesPluginEnv:
    def __init__(self, *, name: builtins.str, value: builtins.str) -> None:
        '''EnvEntry represents an entry in the application's environment.

        :param name: Name is the name of the variable, usually expressed in uppercase.
        :param value: Value is the value of the variable.

        :schema: ApplicationSpecSourcesPluginEnv
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__72cadffb7900ee40f8027d10c925b2fdc554943e8ef1d89c65e2c686c23c14c1)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "value": value,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''Name is the name of the variable, usually expressed in uppercase.

        :schema: ApplicationSpecSourcesPluginEnv#name
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        '''Value is the value of the variable.

        :schema: ApplicationSpecSourcesPluginEnv#value
        '''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesPluginEnv(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSourcesPluginParameters",
    jsii_struct_bases=[],
    name_mapping={"array": "array", "map": "map", "name": "name", "string": "string"},
)
class ApplicationSpecSourcesPluginParameters:
    def __init__(
        self,
        *,
        array: typing.Optional[typing.Sequence[builtins.str]] = None,
        map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        string: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param array: Array is the value of an array type parameter.
        :param map: Map is the value of a map type parameter.
        :param name: Name is the name identifying a parameter.
        :param string: String_ is the value of a string type parameter.

        :schema: ApplicationSpecSourcesPluginParameters
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__22f80ba800846fc0cbd5fadf7ee088450866079e81ba71270c5a031d20757ebd)
            check_type(argname="argument array", value=array, expected_type=type_hints["array"])
            check_type(argname="argument map", value=map, expected_type=type_hints["map"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument string", value=string, expected_type=type_hints["string"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if array is not None:
            self._values["array"] = array
        if map is not None:
            self._values["map"] = map
        if name is not None:
            self._values["name"] = name
        if string is not None:
            self._values["string"] = string

    @builtins.property
    def array(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array is the value of an array type parameter.

        :schema: ApplicationSpecSourcesPluginParameters#array
        '''
        result = self._values.get("array")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def map(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Map is the value of a map type parameter.

        :schema: ApplicationSpecSourcesPluginParameters#map
        '''
        result = self._values.get("map")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Name is the name identifying a parameter.

        :schema: ApplicationSpecSourcesPluginParameters#name
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def string(self) -> typing.Optional[builtins.str]:
        '''String_ is the value of a string type parameter.

        :schema: ApplicationSpecSourcesPluginParameters#string
        '''
        result = self._values.get("string")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSourcesPluginParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSyncPolicy",
    jsii_struct_bases=[],
    name_mapping={
        "automated": "automated",
        "managed_namespace_metadata": "managedNamespaceMetadata",
        "retry": "retry",
        "sync_options": "syncOptions",
    },
)
class ApplicationSpecSyncPolicy:
    def __init__(
        self,
        *,
        automated: typing.Optional[typing.Union["ApplicationSpecSyncPolicyAutomated", typing.Dict[builtins.str, typing.Any]]] = None,
        managed_namespace_metadata: typing.Optional[typing.Union["ApplicationSpecSyncPolicyManagedNamespaceMetadata", typing.Dict[builtins.str, typing.Any]]] = None,
        retry: typing.Optional[typing.Union["ApplicationSpecSyncPolicyRetry", typing.Dict[builtins.str, typing.Any]]] = None,
        sync_options: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''SyncPolicy controls when and how a sync will be performed.

        :param automated: Automated will keep an application synced to the target revision.
        :param managed_namespace_metadata: ManagedNamespaceMetadata controls metadata in the given namespace (if CreateNamespace=true).
        :param retry: Retry controls failed sync retry behavior.
        :param sync_options: Options allow you to specify whole app sync-options.

        :schema: ApplicationSpecSyncPolicy
        '''
        if isinstance(automated, dict):
            automated = ApplicationSpecSyncPolicyAutomated(**automated)
        if isinstance(managed_namespace_metadata, dict):
            managed_namespace_metadata = ApplicationSpecSyncPolicyManagedNamespaceMetadata(**managed_namespace_metadata)
        if isinstance(retry, dict):
            retry = ApplicationSpecSyncPolicyRetry(**retry)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__37ec1e9e8005da2f9d06eb788a8c00a3a2fc731d5f2582b16531ee84aca025b4)
            check_type(argname="argument automated", value=automated, expected_type=type_hints["automated"])
            check_type(argname="argument managed_namespace_metadata", value=managed_namespace_metadata, expected_type=type_hints["managed_namespace_metadata"])
            check_type(argname="argument retry", value=retry, expected_type=type_hints["retry"])
            check_type(argname="argument sync_options", value=sync_options, expected_type=type_hints["sync_options"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if automated is not None:
            self._values["automated"] = automated
        if managed_namespace_metadata is not None:
            self._values["managed_namespace_metadata"] = managed_namespace_metadata
        if retry is not None:
            self._values["retry"] = retry
        if sync_options is not None:
            self._values["sync_options"] = sync_options

    @builtins.property
    def automated(self) -> typing.Optional["ApplicationSpecSyncPolicyAutomated"]:
        '''Automated will keep an application synced to the target revision.

        :schema: ApplicationSpecSyncPolicy#automated
        '''
        result = self._values.get("automated")
        return typing.cast(typing.Optional["ApplicationSpecSyncPolicyAutomated"], result)

    @builtins.property
    def managed_namespace_metadata(
        self,
    ) -> typing.Optional["ApplicationSpecSyncPolicyManagedNamespaceMetadata"]:
        '''ManagedNamespaceMetadata controls metadata in the given namespace (if CreateNamespace=true).

        :schema: ApplicationSpecSyncPolicy#managedNamespaceMetadata
        '''
        result = self._values.get("managed_namespace_metadata")
        return typing.cast(typing.Optional["ApplicationSpecSyncPolicyManagedNamespaceMetadata"], result)

    @builtins.property
    def retry(self) -> typing.Optional["ApplicationSpecSyncPolicyRetry"]:
        '''Retry controls failed sync retry behavior.

        :schema: ApplicationSpecSyncPolicy#retry
        '''
        result = self._values.get("retry")
        return typing.cast(typing.Optional["ApplicationSpecSyncPolicyRetry"], result)

    @builtins.property
    def sync_options(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Options allow you to specify whole app sync-options.

        :schema: ApplicationSpecSyncPolicy#syncOptions
        '''
        result = self._values.get("sync_options")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSyncPolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSyncPolicyAutomated",
    jsii_struct_bases=[],
    name_mapping={
        "allow_empty": "allowEmpty",
        "enabled": "enabled",
        "prune": "prune",
        "self_heal": "selfHeal",
    },
)
class ApplicationSpecSyncPolicyAutomated:
    def __init__(
        self,
        *,
        allow_empty: typing.Optional[builtins.bool] = None,
        enabled: typing.Optional[builtins.bool] = None,
        prune: typing.Optional[builtins.bool] = None,
        self_heal: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Automated will keep an application synced to the target revision.

        :param allow_empty: AllowEmpty allows apps have zero live resources (default: false).
        :param enabled: Enable allows apps to explicitly control automated sync.
        :param prune: Prune specifies whether to delete resources from the cluster that are not found in the sources anymore as part of automated sync (default: false).
        :param self_heal: SelfHeal specifies whether to revert resources back to their desired state upon modification in the cluster (default: false).

        :schema: ApplicationSpecSyncPolicyAutomated
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dff153fe3cbffa991a31c91e3b2f2a0f66ec9020573e30accffb431b4031708f)
            check_type(argname="argument allow_empty", value=allow_empty, expected_type=type_hints["allow_empty"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument prune", value=prune, expected_type=type_hints["prune"])
            check_type(argname="argument self_heal", value=self_heal, expected_type=type_hints["self_heal"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if allow_empty is not None:
            self._values["allow_empty"] = allow_empty
        if enabled is not None:
            self._values["enabled"] = enabled
        if prune is not None:
            self._values["prune"] = prune
        if self_heal is not None:
            self._values["self_heal"] = self_heal

    @builtins.property
    def allow_empty(self) -> typing.Optional[builtins.bool]:
        '''AllowEmpty allows apps have zero live resources (default: false).

        :schema: ApplicationSpecSyncPolicyAutomated#allowEmpty
        '''
        result = self._values.get("allow_empty")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        '''Enable allows apps to explicitly control automated sync.

        :schema: ApplicationSpecSyncPolicyAutomated#enabled
        '''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def prune(self) -> typing.Optional[builtins.bool]:
        '''Prune specifies whether to delete resources from the cluster that are not found in the sources anymore as part of automated sync (default: false).

        :schema: ApplicationSpecSyncPolicyAutomated#prune
        '''
        result = self._values.get("prune")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def self_heal(self) -> typing.Optional[builtins.bool]:
        '''SelfHeal specifies whether to revert resources back to their desired state upon modification in the cluster (default: false).

        :schema: ApplicationSpecSyncPolicyAutomated#selfHeal
        '''
        result = self._values.get("self_heal")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSyncPolicyAutomated(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSyncPolicyManagedNamespaceMetadata",
    jsii_struct_bases=[],
    name_mapping={"annotations": "annotations", "labels": "labels"},
)
class ApplicationSpecSyncPolicyManagedNamespaceMetadata:
    def __init__(
        self,
        *,
        annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''ManagedNamespaceMetadata controls metadata in the given namespace (if CreateNamespace=true).

        :param annotations: 
        :param labels: 

        :schema: ApplicationSpecSyncPolicyManagedNamespaceMetadata
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8a1c41365c489132bf66b23abe0d40fdbd73382b63d5732cb7de799212a23ce2)
            check_type(argname="argument annotations", value=annotations, expected_type=type_hints["annotations"])
            check_type(argname="argument labels", value=labels, expected_type=type_hints["labels"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if annotations is not None:
            self._values["annotations"] = annotations
        if labels is not None:
            self._values["labels"] = labels

    @builtins.property
    def annotations(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''
        :schema: ApplicationSpecSyncPolicyManagedNamespaceMetadata#annotations
        '''
        result = self._values.get("annotations")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def labels(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''
        :schema: ApplicationSpecSyncPolicyManagedNamespaceMetadata#labels
        '''
        result = self._values.get("labels")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSyncPolicyManagedNamespaceMetadata(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSyncPolicyRetry",
    jsii_struct_bases=[],
    name_mapping={"backoff": "backoff", "limit": "limit", "refresh": "refresh"},
)
class ApplicationSpecSyncPolicyRetry:
    def __init__(
        self,
        *,
        backoff: typing.Optional[typing.Union["ApplicationSpecSyncPolicyRetryBackoff", typing.Dict[builtins.str, typing.Any]]] = None,
        limit: typing.Optional[jsii.Number] = None,
        refresh: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Retry controls failed sync retry behavior.

        :param backoff: Backoff controls how to backoff on subsequent retries of failed syncs.
        :param limit: Limit is the maximum number of attempts for retrying a failed sync. If set to 0, no retries will be performed.
        :param refresh: Refresh indicates if the latest revision should be used on retry instead of the initial one (default: false).

        :schema: ApplicationSpecSyncPolicyRetry
        '''
        if isinstance(backoff, dict):
            backoff = ApplicationSpecSyncPolicyRetryBackoff(**backoff)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9056530bc9b98c6462dff4d26f05b391b1eaa261eb2ecf8b0c69bdbb90c09af9)
            check_type(argname="argument backoff", value=backoff, expected_type=type_hints["backoff"])
            check_type(argname="argument limit", value=limit, expected_type=type_hints["limit"])
            check_type(argname="argument refresh", value=refresh, expected_type=type_hints["refresh"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if backoff is not None:
            self._values["backoff"] = backoff
        if limit is not None:
            self._values["limit"] = limit
        if refresh is not None:
            self._values["refresh"] = refresh

    @builtins.property
    def backoff(self) -> typing.Optional["ApplicationSpecSyncPolicyRetryBackoff"]:
        '''Backoff controls how to backoff on subsequent retries of failed syncs.

        :schema: ApplicationSpecSyncPolicyRetry#backoff
        '''
        result = self._values.get("backoff")
        return typing.cast(typing.Optional["ApplicationSpecSyncPolicyRetryBackoff"], result)

    @builtins.property
    def limit(self) -> typing.Optional[jsii.Number]:
        '''Limit is the maximum number of attempts for retrying a failed sync.

        If set to 0, no retries will be performed.

        :schema: ApplicationSpecSyncPolicyRetry#limit
        '''
        result = self._values.get("limit")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def refresh(self) -> typing.Optional[builtins.bool]:
        '''Refresh indicates if the latest revision should be used on retry instead of the initial one (default: false).

        :schema: ApplicationSpecSyncPolicyRetry#refresh
        '''
        result = self._values.get("refresh")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSyncPolicyRetry(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="ioargoproj.ApplicationSpecSyncPolicyRetryBackoff",
    jsii_struct_bases=[],
    name_mapping={
        "duration": "duration",
        "factor": "factor",
        "max_duration": "maxDuration",
    },
)
class ApplicationSpecSyncPolicyRetryBackoff:
    def __init__(
        self,
        *,
        duration: typing.Optional[builtins.str] = None,
        factor: typing.Optional[jsii.Number] = None,
        max_duration: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Backoff controls how to backoff on subsequent retries of failed syncs.

        :param duration: Duration is the amount to back off. Default unit is seconds, but could also be a duration (e.g. "2m", "1h")
        :param factor: Factor is a factor to multiply the base duration after each failed retry.
        :param max_duration: MaxDuration is the maximum amount of time allowed for the backoff strategy.

        :schema: ApplicationSpecSyncPolicyRetryBackoff
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__70fbb090c407cad08c8096da23e6eb65ab2e11b7ad450b134f29f62907170d45)
            check_type(argname="argument duration", value=duration, expected_type=type_hints["duration"])
            check_type(argname="argument factor", value=factor, expected_type=type_hints["factor"])
            check_type(argname="argument max_duration", value=max_duration, expected_type=type_hints["max_duration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if duration is not None:
            self._values["duration"] = duration
        if factor is not None:
            self._values["factor"] = factor
        if max_duration is not None:
            self._values["max_duration"] = max_duration

    @builtins.property
    def duration(self) -> typing.Optional[builtins.str]:
        '''Duration is the amount to back off.

        Default unit is seconds, but could also be a duration (e.g. "2m", "1h")

        :schema: ApplicationSpecSyncPolicyRetryBackoff#duration
        '''
        result = self._values.get("duration")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def factor(self) -> typing.Optional[jsii.Number]:
        '''Factor is a factor to multiply the base duration after each failed retry.

        :schema: ApplicationSpecSyncPolicyRetryBackoff#factor
        '''
        result = self._values.get("factor")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_duration(self) -> typing.Optional[builtins.str]:
        '''MaxDuration is the maximum amount of time allowed for the backoff strategy.

        :schema: ApplicationSpecSyncPolicyRetryBackoff#maxDuration
        '''
        result = self._values.get("max_duration")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApplicationSpecSyncPolicyRetryBackoff(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "Application",
    "ApplicationOperation",
    "ApplicationOperationInfo",
    "ApplicationOperationInitiatedBy",
    "ApplicationOperationRetry",
    "ApplicationOperationRetryBackoff",
    "ApplicationOperationSync",
    "ApplicationOperationSyncResources",
    "ApplicationOperationSyncSource",
    "ApplicationOperationSyncSourceDirectory",
    "ApplicationOperationSyncSourceDirectoryJsonnet",
    "ApplicationOperationSyncSourceDirectoryJsonnetExtVars",
    "ApplicationOperationSyncSourceDirectoryJsonnetTlas",
    "ApplicationOperationSyncSourceHelm",
    "ApplicationOperationSyncSourceHelmFileParameters",
    "ApplicationOperationSyncSourceHelmParameters",
    "ApplicationOperationSyncSourceKustomize",
    "ApplicationOperationSyncSourceKustomizePatches",
    "ApplicationOperationSyncSourceKustomizePatchesTarget",
    "ApplicationOperationSyncSourceKustomizeReplicas",
    "ApplicationOperationSyncSourceKustomizeReplicasCount",
    "ApplicationOperationSyncSourcePlugin",
    "ApplicationOperationSyncSourcePluginEnv",
    "ApplicationOperationSyncSourcePluginParameters",
    "ApplicationOperationSyncSources",
    "ApplicationOperationSyncSourcesDirectory",
    "ApplicationOperationSyncSourcesDirectoryJsonnet",
    "ApplicationOperationSyncSourcesDirectoryJsonnetExtVars",
    "ApplicationOperationSyncSourcesDirectoryJsonnetTlas",
    "ApplicationOperationSyncSourcesHelm",
    "ApplicationOperationSyncSourcesHelmFileParameters",
    "ApplicationOperationSyncSourcesHelmParameters",
    "ApplicationOperationSyncSourcesKustomize",
    "ApplicationOperationSyncSourcesKustomizePatches",
    "ApplicationOperationSyncSourcesKustomizePatchesTarget",
    "ApplicationOperationSyncSourcesKustomizeReplicas",
    "ApplicationOperationSyncSourcesKustomizeReplicasCount",
    "ApplicationOperationSyncSourcesPlugin",
    "ApplicationOperationSyncSourcesPluginEnv",
    "ApplicationOperationSyncSourcesPluginParameters",
    "ApplicationOperationSyncSyncStrategy",
    "ApplicationOperationSyncSyncStrategyApply",
    "ApplicationOperationSyncSyncStrategyHook",
    "ApplicationProps",
    "ApplicationSpec",
    "ApplicationSpecDestination",
    "ApplicationSpecIgnoreDifferences",
    "ApplicationSpecInfo",
    "ApplicationSpecSource",
    "ApplicationSpecSourceDirectory",
    "ApplicationSpecSourceDirectoryJsonnet",
    "ApplicationSpecSourceDirectoryJsonnetExtVars",
    "ApplicationSpecSourceDirectoryJsonnetTlas",
    "ApplicationSpecSourceHelm",
    "ApplicationSpecSourceHelmFileParameters",
    "ApplicationSpecSourceHelmParameters",
    "ApplicationSpecSourceHydrator",
    "ApplicationSpecSourceHydratorDrySource",
    "ApplicationSpecSourceHydratorHydrateTo",
    "ApplicationSpecSourceHydratorSyncSource",
    "ApplicationSpecSourceKustomize",
    "ApplicationSpecSourceKustomizePatches",
    "ApplicationSpecSourceKustomizePatchesTarget",
    "ApplicationSpecSourceKustomizeReplicas",
    "ApplicationSpecSourceKustomizeReplicasCount",
    "ApplicationSpecSourcePlugin",
    "ApplicationSpecSourcePluginEnv",
    "ApplicationSpecSourcePluginParameters",
    "ApplicationSpecSources",
    "ApplicationSpecSourcesDirectory",
    "ApplicationSpecSourcesDirectoryJsonnet",
    "ApplicationSpecSourcesDirectoryJsonnetExtVars",
    "ApplicationSpecSourcesDirectoryJsonnetTlas",
    "ApplicationSpecSourcesHelm",
    "ApplicationSpecSourcesHelmFileParameters",
    "ApplicationSpecSourcesHelmParameters",
    "ApplicationSpecSourcesKustomize",
    "ApplicationSpecSourcesKustomizePatches",
    "ApplicationSpecSourcesKustomizePatchesTarget",
    "ApplicationSpecSourcesKustomizeReplicas",
    "ApplicationSpecSourcesKustomizeReplicasCount",
    "ApplicationSpecSourcesPlugin",
    "ApplicationSpecSourcesPluginEnv",
    "ApplicationSpecSourcesPluginParameters",
    "ApplicationSpecSyncPolicy",
    "ApplicationSpecSyncPolicyAutomated",
    "ApplicationSpecSyncPolicyManagedNamespaceMetadata",
    "ApplicationSpecSyncPolicyRetry",
    "ApplicationSpecSyncPolicyRetryBackoff",
]

publication.publish()

def _typecheckingstub__9fadc55084560f240c2c9e6a99b09bb072446fb64fdbc835fefe1e6223a2cc52(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    metadata: typing.Union[_cdk8s_d3d9af27.ApiObjectMetadata, typing.Dict[builtins.str, typing.Any]],
    spec: typing.Union[ApplicationSpec, typing.Dict[builtins.str, typing.Any]],
    operation: typing.Optional[typing.Union[ApplicationOperation, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fc7489c6e9afd59a19ebe90297e21cd3b82fa6c82434517bb3ec2d7714eaa981(
    *,
    info: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationInfo, typing.Dict[builtins.str, typing.Any]]]] = None,
    initiated_by: typing.Optional[typing.Union[ApplicationOperationInitiatedBy, typing.Dict[builtins.str, typing.Any]]] = None,
    retry: typing.Optional[typing.Union[ApplicationOperationRetry, typing.Dict[builtins.str, typing.Any]]] = None,
    sync: typing.Optional[typing.Union[ApplicationOperationSync, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d9d029733dc89d70b49466bd73599fc2cbabade797ce042fdc2d5e7fc8bbb145(
    *,
    name: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ebb4ba1ffa2baf2a89537dc6954e1da91dc957dd881e0b03f84263feaca63e80(
    *,
    automated: typing.Optional[builtins.bool] = None,
    username: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4ac6fe22df0bbd4d619fea202e4f3000095deed912da8875517926ae5f30ece5(
    *,
    backoff: typing.Optional[typing.Union[ApplicationOperationRetryBackoff, typing.Dict[builtins.str, typing.Any]]] = None,
    limit: typing.Optional[jsii.Number] = None,
    refresh: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e0275a64a928a93eea988e920bdff4cf240f265cb687299af5c4a92644eb5d7b(
    *,
    duration: typing.Optional[builtins.str] = None,
    factor: typing.Optional[jsii.Number] = None,
    max_duration: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a6298dfe0e54c7f7cb26e8308cab95d46ae758c3f7c7d8ec80166d4234e79be7(
    *,
    auto_heal_attempts_count: typing.Optional[jsii.Number] = None,
    dry_run: typing.Optional[builtins.bool] = None,
    manifests: typing.Optional[typing.Sequence[builtins.str]] = None,
    prune: typing.Optional[builtins.bool] = None,
    resources: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncResources, typing.Dict[builtins.str, typing.Any]]]] = None,
    revision: typing.Optional[builtins.str] = None,
    revisions: typing.Optional[typing.Sequence[builtins.str]] = None,
    source: typing.Optional[typing.Union[ApplicationOperationSyncSource, typing.Dict[builtins.str, typing.Any]]] = None,
    sources: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSources, typing.Dict[builtins.str, typing.Any]]]] = None,
    sync_options: typing.Optional[typing.Sequence[builtins.str]] = None,
    sync_strategy: typing.Optional[typing.Union[ApplicationOperationSyncSyncStrategy, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__57c79a8c21b61f24d9d60f6ab430d024ad1062593420b1cc70bbcab5ad0251ee(
    *,
    kind: builtins.str,
    name: builtins.str,
    group: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__380a721d40f74f3998504dda80bc9fbf987a3ececf1c01c3c1316da13bf2f238(
    *,
    repo_url: builtins.str,
    chart: typing.Optional[builtins.str] = None,
    directory: typing.Optional[typing.Union[ApplicationOperationSyncSourceDirectory, typing.Dict[builtins.str, typing.Any]]] = None,
    helm: typing.Optional[typing.Union[ApplicationOperationSyncSourceHelm, typing.Dict[builtins.str, typing.Any]]] = None,
    kustomize: typing.Optional[typing.Union[ApplicationOperationSyncSourceKustomize, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    plugin: typing.Optional[typing.Union[ApplicationOperationSyncSourcePlugin, typing.Dict[builtins.str, typing.Any]]] = None,
    ref: typing.Optional[builtins.str] = None,
    target_revision: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__68dd854000d14031a8145af1c8c3ddaf12c86dd9ecc65104616e077a2172579a(
    *,
    exclude: typing.Optional[builtins.str] = None,
    include: typing.Optional[builtins.str] = None,
    jsonnet: typing.Optional[typing.Union[ApplicationOperationSyncSourceDirectoryJsonnet, typing.Dict[builtins.str, typing.Any]]] = None,
    recurse: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8252a821d880e55f2ed4fc9fa8d53507d0a79edefdfb3568350ba31c19e8e6b6(
    *,
    ext_vars: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourceDirectoryJsonnetExtVars, typing.Dict[builtins.str, typing.Any]]]] = None,
    libs: typing.Optional[typing.Sequence[builtins.str]] = None,
    tlas: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourceDirectoryJsonnetTlas, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__966c0a7acfd38fe0dce9dbf0d8bdd38f51b40bc26789ce769399c983ad046f32(
    *,
    name: builtins.str,
    value: builtins.str,
    code: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c0c87bea537ea3fd2aa5b34f35cbe7f666f5d15a2ddc3b382248bc32490d4832(
    *,
    name: builtins.str,
    value: builtins.str,
    code: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b386c667b68ec553767e009262cc57f6b9dd41e43536fc3d79443da816b4ae76(
    *,
    api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
    file_parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourceHelmFileParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_missing_value_files: typing.Optional[builtins.bool] = None,
    kube_version: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourceHelmParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
    pass_credentials: typing.Optional[builtins.bool] = None,
    release_name: typing.Optional[builtins.str] = None,
    skip_crds: typing.Optional[builtins.bool] = None,
    skip_schema_validation: typing.Optional[builtins.bool] = None,
    skip_tests: typing.Optional[builtins.bool] = None,
    value_files: typing.Optional[typing.Sequence[builtins.str]] = None,
    values: typing.Optional[builtins.str] = None,
    values_object: typing.Any = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bda8f2463180d72c0afdd472e8d7562b7f94b54167bbff1ef898c73de3218c9b(
    *,
    name: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ac77b224717d4ca6dae0e47a49730c4a858ab4ae9672d7ab36360686bb3442d8(
    *,
    force_string: typing.Optional[builtins.bool] = None,
    name: typing.Optional[builtins.str] = None,
    value: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b738b3c037af039c4d26e237b22edf72e087f17f848436770e7d91aa35803be(
    *,
    api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
    common_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    common_annotations_envsubst: typing.Optional[builtins.bool] = None,
    common_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    components: typing.Optional[typing.Sequence[builtins.str]] = None,
    force_common_annotations: typing.Optional[builtins.bool] = None,
    force_common_labels: typing.Optional[builtins.bool] = None,
    ignore_missing_components: typing.Optional[builtins.bool] = None,
    images: typing.Optional[typing.Sequence[builtins.str]] = None,
    kube_version: typing.Optional[builtins.str] = None,
    label_include_templates: typing.Optional[builtins.bool] = None,
    label_without_selector: typing.Optional[builtins.bool] = None,
    name_prefix: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    name_suffix: typing.Optional[builtins.str] = None,
    patches: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourceKustomizePatches, typing.Dict[builtins.str, typing.Any]]]] = None,
    replicas: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourceKustomizeReplicas, typing.Dict[builtins.str, typing.Any]]]] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__403d98dbeb14f0d44b70e8177847cac9923ac145b2bedcf54c929d57c91d07f3(
    *,
    options: typing.Optional[typing.Mapping[builtins.str, builtins.bool]] = None,
    patch: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    target: typing.Optional[typing.Union[ApplicationOperationSyncSourceKustomizePatchesTarget, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__45dc4ffc9c41609070e18c4045a1fd3469f2771b2f5a70d08b8029fc6a090036(
    *,
    annotation_selector: typing.Optional[builtins.str] = None,
    group: typing.Optional[builtins.str] = None,
    kind: typing.Optional[builtins.str] = None,
    label_selector: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5bcfa17d48c31956a1583c4b8e33c2236f203e85774d1972c956f7e4d0408c47(
    *,
    count: ApplicationOperationSyncSourceKustomizeReplicasCount,
    name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__353ac407776b154158bf4858074912a6ab4bb0e6505180220b0a9389af131e28(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0396193d2a74e325951a6b23c7478a300a48ae901e7b6dcdd57ee2f9ef65e360(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b963da857103b74fb6dd9321f58bbec9ef78c44c0c7c7001fc7a5a40a45ab57e(
    *,
    env: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcePluginEnv, typing.Dict[builtins.str, typing.Any]]]] = None,
    name: typing.Optional[builtins.str] = None,
    parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcePluginParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bac56bca7082a809be909907326178a0ef4bcd363c89b646e42378bbe3b80e2c(
    *,
    name: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7720bb9e4d0879b72177070fac6d572303d14b0a3dfca7a0b6acb7d254940def(
    *,
    array: typing.Optional[typing.Sequence[builtins.str]] = None,
    map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    string: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__131a3b605137deb720d23b45b3ff58347f2c9100e00540ecdfef615ebf73e4ca(
    *,
    repo_url: builtins.str,
    chart: typing.Optional[builtins.str] = None,
    directory: typing.Optional[typing.Union[ApplicationOperationSyncSourcesDirectory, typing.Dict[builtins.str, typing.Any]]] = None,
    helm: typing.Optional[typing.Union[ApplicationOperationSyncSourcesHelm, typing.Dict[builtins.str, typing.Any]]] = None,
    kustomize: typing.Optional[typing.Union[ApplicationOperationSyncSourcesKustomize, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    plugin: typing.Optional[typing.Union[ApplicationOperationSyncSourcesPlugin, typing.Dict[builtins.str, typing.Any]]] = None,
    ref: typing.Optional[builtins.str] = None,
    target_revision: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a46a3325ca7605bd9bd99a6a11f526fc19811dbd541f621a7808ae67cdc6ad06(
    *,
    exclude: typing.Optional[builtins.str] = None,
    include: typing.Optional[builtins.str] = None,
    jsonnet: typing.Optional[typing.Union[ApplicationOperationSyncSourcesDirectoryJsonnet, typing.Dict[builtins.str, typing.Any]]] = None,
    recurse: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__87d35197c04ba87c1a789fa31c8888a79d40cc1f7cb28ab4376ac20fa408da4e(
    *,
    ext_vars: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcesDirectoryJsonnetExtVars, typing.Dict[builtins.str, typing.Any]]]] = None,
    libs: typing.Optional[typing.Sequence[builtins.str]] = None,
    tlas: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcesDirectoryJsonnetTlas, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f845fe54066037fc6f242f792fba6bf3dd774271a8b0016ead34aa68b9495502(
    *,
    name: builtins.str,
    value: builtins.str,
    code: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__119ae484e7760b7c5e5c31d6da4e48022a181b8a8349c4b575999fd8dcffefd9(
    *,
    name: builtins.str,
    value: builtins.str,
    code: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__172ec38f042e07af6143f0fbd294bba3113923d59563a3a268a2bd4efe74d50d(
    *,
    api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
    file_parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcesHelmFileParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_missing_value_files: typing.Optional[builtins.bool] = None,
    kube_version: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcesHelmParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
    pass_credentials: typing.Optional[builtins.bool] = None,
    release_name: typing.Optional[builtins.str] = None,
    skip_crds: typing.Optional[builtins.bool] = None,
    skip_schema_validation: typing.Optional[builtins.bool] = None,
    skip_tests: typing.Optional[builtins.bool] = None,
    value_files: typing.Optional[typing.Sequence[builtins.str]] = None,
    values: typing.Optional[builtins.str] = None,
    values_object: typing.Any = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__deb5d515c7d023132be81c0369a565e64264d605fa91e5fbed6f7f94ba0170ad(
    *,
    name: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__39bf4f2b544187283cac9d2abd9e46d60c344009202a4ac76c70bbc6c4cce358(
    *,
    force_string: typing.Optional[builtins.bool] = None,
    name: typing.Optional[builtins.str] = None,
    value: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__79be8f5bac148dd707962053a8ca1de26f8110b882327403e40e1b6d86abe2e7(
    *,
    api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
    common_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    common_annotations_envsubst: typing.Optional[builtins.bool] = None,
    common_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    components: typing.Optional[typing.Sequence[builtins.str]] = None,
    force_common_annotations: typing.Optional[builtins.bool] = None,
    force_common_labels: typing.Optional[builtins.bool] = None,
    ignore_missing_components: typing.Optional[builtins.bool] = None,
    images: typing.Optional[typing.Sequence[builtins.str]] = None,
    kube_version: typing.Optional[builtins.str] = None,
    label_include_templates: typing.Optional[builtins.bool] = None,
    label_without_selector: typing.Optional[builtins.bool] = None,
    name_prefix: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    name_suffix: typing.Optional[builtins.str] = None,
    patches: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcesKustomizePatches, typing.Dict[builtins.str, typing.Any]]]] = None,
    replicas: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcesKustomizeReplicas, typing.Dict[builtins.str, typing.Any]]]] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__35d939365f71fe69445ede174ee8ec31bc6cc3e80247f046e0224c51a5462014(
    *,
    options: typing.Optional[typing.Mapping[builtins.str, builtins.bool]] = None,
    patch: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    target: typing.Optional[typing.Union[ApplicationOperationSyncSourcesKustomizePatchesTarget, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__83a5f7991cb91a81bade59aca319c06a7a8d514661075fb6cf2d5b9a87b695d3(
    *,
    annotation_selector: typing.Optional[builtins.str] = None,
    group: typing.Optional[builtins.str] = None,
    kind: typing.Optional[builtins.str] = None,
    label_selector: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e90621a15a04d2a0abf5ad20f8a2278f407c66feb183be6418300bd5505a54c1(
    *,
    count: ApplicationOperationSyncSourcesKustomizeReplicasCount,
    name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40bc0586fcf2db62ae35e6b94c7a27ad159b312b7d1884ce1c1e01a7eee59271(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__833a26a87ec1d217269e4e8f93f71e9ab97901518350c8420bf4fb6208c411dc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__21184de0aef8faddfe3a2c91cea28a1d6c60985733e822046dfc080e4d1e777f(
    *,
    env: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcesPluginEnv, typing.Dict[builtins.str, typing.Any]]]] = None,
    name: typing.Optional[builtins.str] = None,
    parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationOperationSyncSourcesPluginParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b4d2c4cecda1d8199b9061516e8bd0af91b9461eb3ebb25f303e38603445162(
    *,
    name: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b31e1c1123fd42d5ebe1ee1cc773723f111f370a9979ada34364ead2f6781366(
    *,
    array: typing.Optional[typing.Sequence[builtins.str]] = None,
    map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    string: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eeac69098ed9b189e55486c4c824870596c6d1bfa56e5ac75b42a9922a978241(
    *,
    apply: typing.Optional[typing.Union[ApplicationOperationSyncSyncStrategyApply, typing.Dict[builtins.str, typing.Any]]] = None,
    hook: typing.Optional[typing.Union[ApplicationOperationSyncSyncStrategyHook, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5dffa8693690076d84c566d163f7109d618d9bc491d9af0acaade089d1893aef(
    *,
    force: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__232a28768e1b1149f33f9cc4efb2f315e3722f3c5e4472c896498c818abee5e0(
    *,
    force: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5ca23bf220d592849372e0bd99f10e3ce28c86c57e545253a959e91aed82183a(
    *,
    metadata: typing.Union[_cdk8s_d3d9af27.ApiObjectMetadata, typing.Dict[builtins.str, typing.Any]],
    spec: typing.Union[ApplicationSpec, typing.Dict[builtins.str, typing.Any]],
    operation: typing.Optional[typing.Union[ApplicationOperation, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a1f307d49d2573da0fdf411f65384f1f5e43cfe5199a85fa3476e965a2efcc9f(
    *,
    destination: typing.Union[ApplicationSpecDestination, typing.Dict[builtins.str, typing.Any]],
    project: builtins.str,
    ignore_differences: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecIgnoreDifferences, typing.Dict[builtins.str, typing.Any]]]] = None,
    info: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecInfo, typing.Dict[builtins.str, typing.Any]]]] = None,
    revision_history_limit: typing.Optional[jsii.Number] = None,
    source: typing.Optional[typing.Union[ApplicationSpecSource, typing.Dict[builtins.str, typing.Any]]] = None,
    source_hydrator: typing.Optional[typing.Union[ApplicationSpecSourceHydrator, typing.Dict[builtins.str, typing.Any]]] = None,
    sources: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSources, typing.Dict[builtins.str, typing.Any]]]] = None,
    sync_policy: typing.Optional[typing.Union[ApplicationSpecSyncPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9238a4351184347c423d2fe1d83049e3b26008d848bd55db0649cec36ea400cc(
    *,
    name: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    server: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__574c58e871387b541eae3bcf761bc3c157e86a493ef79d8c8c05cc54c889338b(
    *,
    kind: builtins.str,
    group: typing.Optional[builtins.str] = None,
    jq_path_expressions: typing.Optional[typing.Sequence[builtins.str]] = None,
    json_pointers: typing.Optional[typing.Sequence[builtins.str]] = None,
    managed_fields_managers: typing.Optional[typing.Sequence[builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__61d3a998a82bb4d85a0cbfb424d45a51c96c47eb4b834a2c399bf783d175a647(
    *,
    name: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9e157c6d056b54b1b5d1fbf7e83e1fc4beeddb70bdce85c5f9d6a7eefb0b149f(
    *,
    repo_url: builtins.str,
    chart: typing.Optional[builtins.str] = None,
    directory: typing.Optional[typing.Union[ApplicationSpecSourceDirectory, typing.Dict[builtins.str, typing.Any]]] = None,
    helm: typing.Optional[typing.Union[ApplicationSpecSourceHelm, typing.Dict[builtins.str, typing.Any]]] = None,
    kustomize: typing.Optional[typing.Union[ApplicationSpecSourceKustomize, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    plugin: typing.Optional[typing.Union[ApplicationSpecSourcePlugin, typing.Dict[builtins.str, typing.Any]]] = None,
    ref: typing.Optional[builtins.str] = None,
    target_revision: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fefb1318b48ea3fb382bc321682e8a64abdc9207410353cc534e21613fdb026e(
    *,
    exclude: typing.Optional[builtins.str] = None,
    include: typing.Optional[builtins.str] = None,
    jsonnet: typing.Optional[typing.Union[ApplicationSpecSourceDirectoryJsonnet, typing.Dict[builtins.str, typing.Any]]] = None,
    recurse: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1d9ee2168d505513d2adfe23f15ef2bd0f287cc883a3bed308c75211a57ddaf2(
    *,
    ext_vars: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourceDirectoryJsonnetExtVars, typing.Dict[builtins.str, typing.Any]]]] = None,
    libs: typing.Optional[typing.Sequence[builtins.str]] = None,
    tlas: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourceDirectoryJsonnetTlas, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e483cf00940264ac67776c440bb705233ad665f91518ff22fd686da8e5fa920d(
    *,
    name: builtins.str,
    value: builtins.str,
    code: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__23a8df3f1e29d28a29abd9689aaca70ce6d998c6b6a143470b15e0bb4bcde305(
    *,
    name: builtins.str,
    value: builtins.str,
    code: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c8e613a2adc9ba39f281a30a94252f51b6222660f9b4ffddfbe53ea8e6648238(
    *,
    api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
    file_parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourceHelmFileParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_missing_value_files: typing.Optional[builtins.bool] = None,
    kube_version: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourceHelmParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
    pass_credentials: typing.Optional[builtins.bool] = None,
    release_name: typing.Optional[builtins.str] = None,
    skip_crds: typing.Optional[builtins.bool] = None,
    skip_schema_validation: typing.Optional[builtins.bool] = None,
    skip_tests: typing.Optional[builtins.bool] = None,
    value_files: typing.Optional[typing.Sequence[builtins.str]] = None,
    values: typing.Optional[builtins.str] = None,
    values_object: typing.Any = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8346dcda3d2bf59be52a4b4202b835794b0570f15154850d4a7a89ed67e802e1(
    *,
    name: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__17a5ce92a0f0e0c91bd2a36e1146c8eabaa0b69b93d5fb75fdeaf97cd1d288b5(
    *,
    force_string: typing.Optional[builtins.bool] = None,
    name: typing.Optional[builtins.str] = None,
    value: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__75adc1cbe17b67a5524593319046518279392ab75ca34ccadb0ea819ac1118e9(
    *,
    dry_source: typing.Union[ApplicationSpecSourceHydratorDrySource, typing.Dict[builtins.str, typing.Any]],
    sync_source: typing.Union[ApplicationSpecSourceHydratorSyncSource, typing.Dict[builtins.str, typing.Any]],
    hydrate_to: typing.Optional[typing.Union[ApplicationSpecSourceHydratorHydrateTo, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ec68ad68d4119003f20c64caa9dc260c146a7a752b739e50490c695975353cd6(
    *,
    path: builtins.str,
    repo_url: builtins.str,
    target_revision: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e970d9eb63dc5fabee5daa8e34fd18483c489f6644799712804d76dab7c380a5(
    *,
    target_branch: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__add5badb0c8beefd8c8f5c21ee57af7fc7131958e07635aa1a79cd7f39defc86(
    *,
    path: builtins.str,
    target_branch: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2607d3d54e995cb9b20e089324cc22c5307e97d282257346f223af8e215c526f(
    *,
    api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
    common_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    common_annotations_envsubst: typing.Optional[builtins.bool] = None,
    common_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    components: typing.Optional[typing.Sequence[builtins.str]] = None,
    force_common_annotations: typing.Optional[builtins.bool] = None,
    force_common_labels: typing.Optional[builtins.bool] = None,
    ignore_missing_components: typing.Optional[builtins.bool] = None,
    images: typing.Optional[typing.Sequence[builtins.str]] = None,
    kube_version: typing.Optional[builtins.str] = None,
    label_include_templates: typing.Optional[builtins.bool] = None,
    label_without_selector: typing.Optional[builtins.bool] = None,
    name_prefix: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    name_suffix: typing.Optional[builtins.str] = None,
    patches: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourceKustomizePatches, typing.Dict[builtins.str, typing.Any]]]] = None,
    replicas: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourceKustomizeReplicas, typing.Dict[builtins.str, typing.Any]]]] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70b3e23903fafbd4c0887ff80abfab919b983639ed51c0f76a8c7a47a856c86b(
    *,
    options: typing.Optional[typing.Mapping[builtins.str, builtins.bool]] = None,
    patch: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    target: typing.Optional[typing.Union[ApplicationSpecSourceKustomizePatchesTarget, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b62415e715ebe025216d418440b87bae78b134fba99998197a8dffb31d81b80b(
    *,
    annotation_selector: typing.Optional[builtins.str] = None,
    group: typing.Optional[builtins.str] = None,
    kind: typing.Optional[builtins.str] = None,
    label_selector: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ced0c644f1f537b52c04c7db8bf6eef78afae7fbfeee7dc051ee2c2ce2ec950a(
    *,
    count: ApplicationSpecSourceKustomizeReplicasCount,
    name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__00f1036b4458a51e88bb4c3f0c8943db31b96eea58341cd262de700602ee9302(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d40c09d2e240a188b5984013a55672fb3d4cd562976a6abf94d26e9516d03669(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__514024456f47697dcd1485e829ac7254241e1fc9c237d237549e6814f0ca49b2(
    *,
    env: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcePluginEnv, typing.Dict[builtins.str, typing.Any]]]] = None,
    name: typing.Optional[builtins.str] = None,
    parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcePluginParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1ae2d9b6c9043f55f847eead5bf3a3fa62a6f74f130064c7bbefd9dbf44ec411(
    *,
    name: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__67737a8e23a311401126a8ec69020232f8542fd2b263bea6431b759be0573142(
    *,
    array: typing.Optional[typing.Sequence[builtins.str]] = None,
    map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    string: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bc297ba23db9492421203bf6aed690cb8adc0c3321300e18c1e75b6c159fcc7c(
    *,
    repo_url: builtins.str,
    chart: typing.Optional[builtins.str] = None,
    directory: typing.Optional[typing.Union[ApplicationSpecSourcesDirectory, typing.Dict[builtins.str, typing.Any]]] = None,
    helm: typing.Optional[typing.Union[ApplicationSpecSourcesHelm, typing.Dict[builtins.str, typing.Any]]] = None,
    kustomize: typing.Optional[typing.Union[ApplicationSpecSourcesKustomize, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    plugin: typing.Optional[typing.Union[ApplicationSpecSourcesPlugin, typing.Dict[builtins.str, typing.Any]]] = None,
    ref: typing.Optional[builtins.str] = None,
    target_revision: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__378b764eb0eac08e33cdb65d1987cfbe7b054de9f12a072b3426e2bf51e5f9c0(
    *,
    exclude: typing.Optional[builtins.str] = None,
    include: typing.Optional[builtins.str] = None,
    jsonnet: typing.Optional[typing.Union[ApplicationSpecSourcesDirectoryJsonnet, typing.Dict[builtins.str, typing.Any]]] = None,
    recurse: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7d77b294df6b010096428e2c6294e171281911fbfae7aca5359c43f32bc0461(
    *,
    ext_vars: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcesDirectoryJsonnetExtVars, typing.Dict[builtins.str, typing.Any]]]] = None,
    libs: typing.Optional[typing.Sequence[builtins.str]] = None,
    tlas: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcesDirectoryJsonnetTlas, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__845dd159a281f4bf8d3ea96f5ae116bc3e010f1ed417747aab930c910555613c(
    *,
    name: builtins.str,
    value: builtins.str,
    code: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a2c5c54f2e2f92a477a591ee6b87292e5000ea574fb8b3ea0864194d159d0ee6(
    *,
    name: builtins.str,
    value: builtins.str,
    code: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__31ab5c861d3f1bd80908a8acea70c092f42f8da0189b0888973af0bdacfa163d(
    *,
    api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
    file_parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcesHelmFileParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_missing_value_files: typing.Optional[builtins.bool] = None,
    kube_version: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcesHelmParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
    pass_credentials: typing.Optional[builtins.bool] = None,
    release_name: typing.Optional[builtins.str] = None,
    skip_crds: typing.Optional[builtins.bool] = None,
    skip_schema_validation: typing.Optional[builtins.bool] = None,
    skip_tests: typing.Optional[builtins.bool] = None,
    value_files: typing.Optional[typing.Sequence[builtins.str]] = None,
    values: typing.Optional[builtins.str] = None,
    values_object: typing.Any = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3591c6b32ad894aa4b81618948d9d1e77dbf3cc1cb1de9eff3b9c92ce2dc199d(
    *,
    name: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a9024cde9c2ff5ca9b5f536937ed4dc212d6b6100b40e97306fd954dfaddf6c2(
    *,
    force_string: typing.Optional[builtins.bool] = None,
    name: typing.Optional[builtins.str] = None,
    value: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0ac1b1f59ae49a9d56c4cfacc0c940b516a5e8081676741e72b08c59feb6c0f5(
    *,
    api_versions: typing.Optional[typing.Sequence[builtins.str]] = None,
    common_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    common_annotations_envsubst: typing.Optional[builtins.bool] = None,
    common_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    components: typing.Optional[typing.Sequence[builtins.str]] = None,
    force_common_annotations: typing.Optional[builtins.bool] = None,
    force_common_labels: typing.Optional[builtins.bool] = None,
    ignore_missing_components: typing.Optional[builtins.bool] = None,
    images: typing.Optional[typing.Sequence[builtins.str]] = None,
    kube_version: typing.Optional[builtins.str] = None,
    label_include_templates: typing.Optional[builtins.bool] = None,
    label_without_selector: typing.Optional[builtins.bool] = None,
    name_prefix: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    name_suffix: typing.Optional[builtins.str] = None,
    patches: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcesKustomizePatches, typing.Dict[builtins.str, typing.Any]]]] = None,
    replicas: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcesKustomizeReplicas, typing.Dict[builtins.str, typing.Any]]]] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ffa8c76ef3ae39471dde2a8af16df254b34a7f5069f06dc2fd59980ee4d89048(
    *,
    options: typing.Optional[typing.Mapping[builtins.str, builtins.bool]] = None,
    patch: typing.Optional[builtins.str] = None,
    path: typing.Optional[builtins.str] = None,
    target: typing.Optional[typing.Union[ApplicationSpecSourcesKustomizePatchesTarget, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5869f465abbf268cc52d050c076351daae4e722d61fdeef9584c9c55514d687d(
    *,
    annotation_selector: typing.Optional[builtins.str] = None,
    group: typing.Optional[builtins.str] = None,
    kind: typing.Optional[builtins.str] = None,
    label_selector: typing.Optional[builtins.str] = None,
    name: typing.Optional[builtins.str] = None,
    namespace: typing.Optional[builtins.str] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a9b8a1ae0df6140ebcd9dbe74b71d52f20ebfbae415fa412b8ee093bdc6f8b52(
    *,
    count: ApplicationSpecSourcesKustomizeReplicasCount,
    name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b3049c79710732ba890aabc204a39455b860b0661ca354f765f2ab4c0286d4aa(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__076d3e9a255054ef7b8b9de93f5f3f5bf95d4c1925ca7269ae7cdb08bb33ec77(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__89df259930d4320290e71fd7d731a9ceb29ffe1e62151cc3172d6419e96e0787(
    *,
    env: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcesPluginEnv, typing.Dict[builtins.str, typing.Any]]]] = None,
    name: typing.Optional[builtins.str] = None,
    parameters: typing.Optional[typing.Sequence[typing.Union[ApplicationSpecSourcesPluginParameters, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__72cadffb7900ee40f8027d10c925b2fdc554943e8ef1d89c65e2c686c23c14c1(
    *,
    name: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__22f80ba800846fc0cbd5fadf7ee088450866079e81ba71270c5a031d20757ebd(
    *,
    array: typing.Optional[typing.Sequence[builtins.str]] = None,
    map: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    string: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__37ec1e9e8005da2f9d06eb788a8c00a3a2fc731d5f2582b16531ee84aca025b4(
    *,
    automated: typing.Optional[typing.Union[ApplicationSpecSyncPolicyAutomated, typing.Dict[builtins.str, typing.Any]]] = None,
    managed_namespace_metadata: typing.Optional[typing.Union[ApplicationSpecSyncPolicyManagedNamespaceMetadata, typing.Dict[builtins.str, typing.Any]]] = None,
    retry: typing.Optional[typing.Union[ApplicationSpecSyncPolicyRetry, typing.Dict[builtins.str, typing.Any]]] = None,
    sync_options: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dff153fe3cbffa991a31c91e3b2f2a0f66ec9020573e30accffb431b4031708f(
    *,
    allow_empty: typing.Optional[builtins.bool] = None,
    enabled: typing.Optional[builtins.bool] = None,
    prune: typing.Optional[builtins.bool] = None,
    self_heal: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8a1c41365c489132bf66b23abe0d40fdbd73382b63d5732cb7de799212a23ce2(
    *,
    annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9056530bc9b98c6462dff4d26f05b391b1eaa261eb2ecf8b0c69bdbb90c09af9(
    *,
    backoff: typing.Optional[typing.Union[ApplicationSpecSyncPolicyRetryBackoff, typing.Dict[builtins.str, typing.Any]]] = None,
    limit: typing.Optional[jsii.Number] = None,
    refresh: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70fbb090c407cad08c8096da23e6eb65ab2e11b7ad450b134f29f62907170d45(
    *,
    duration: typing.Optional[builtins.str] = None,
    factor: typing.Optional[jsii.Number] = None,
    max_duration: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
