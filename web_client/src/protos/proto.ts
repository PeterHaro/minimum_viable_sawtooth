import protobuf from "protobufjs";
import * as appProtoJson from "./generated_protos.json" ;
import * as sdkProtoJson from "./sdk_protos.json" ;

// Compile Application Protobufs
const app_root = protobuf.Root.fromJSON(appProtoJson);
export const SCPayload = app_root.lookup('SCPayload');
export const PropertyValue = app_root.lookup('PropertyValue');
export const PropertySchema = app_root.lookup('PropertySchema');
export const Location = app_root.lookup('Location');
export const Proposal = app_root.lookup('Proposal');

const sdk_root = protobuf.Root.fromJSON(sdkProtoJson);
export const Transaction = sdk_root.lookup('Transaction');