[**@celestoai/celesto**](../README.md)

______________________________________________________________________

[@celestoai/celesto](../README.md) / NetworkPolicy

# Type Alias: NetworkPolicy

> **NetworkPolicy** = { `mode`: `"open"`; } | { `mode`: `"off"`; } | { `allowedCidrs`: readonly `string`\[\]; `mode`: `"restricted"`; }

Controls which outbound IPv4 connections a new sandbox may make.
