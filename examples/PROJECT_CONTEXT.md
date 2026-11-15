# Example project

## Purpose

A small service converts incoming webhook events into queued jobs.

## Running and checking it

The README lists startup commands and the smoke test. Verify that a test webhook reaches the worker before closing a change to the event flow.

## Current work

The retry change is in the working tree. Verify idempotency for a repeated event before deployment.
