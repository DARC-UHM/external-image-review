#!/usr/bin/env bash

gunicorn server:app -b :8070

