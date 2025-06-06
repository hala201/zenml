{{/*
Expand the name of the chart.
*/}}
{{- define "zenml.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "zenml.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "zenml.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "zenml.labels" -}}
helm.sh/chart: {{ include "zenml.chart" . }}
{{ include "zenml.selectorLabels" . }}
{{- if .Chart.Version }}
app.kubernetes.io/version: {{ .Chart.Version | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "zenml.selectorLabels" -}}
app.kubernetes.io/name: {{ include "zenml.name" . }}
{{- if .Values.zenml.instanceLabel }}
app.kubernetes.io/instance: {{ .Values.zenml.instanceLabel | quote }}
{{- else }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "zenml.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "zenml.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Build the complete NO_PROXY list
*/}}
{{- define "zenml.noProxyList" -}}
{{- $noProxy := .Values.zenml.proxy.noProxy -}}
{{- /* Add the server URL hostname */ -}}
{{- if .Values.zenml.serverURL -}}
{{- $serverURL := urlParse .Values.zenml.serverURL -}}
{{- if not (contains $serverURL.host $noProxy) -}}
{{- $noProxy = printf "%s,%s" $noProxy $serverURL.host -}}
{{- end -}}
{{- end -}}
{{- /* Add the ingress hostname if specified */ -}}
{{- if .Values.zenml.ingress.host -}}
{{- if not (contains .Values.zenml.ingress.host $noProxy) -}}
{{- $noProxy = printf "%s,%s" $noProxy .Values.zenml.ingress.host -}}
{{- end -}}
{{- end -}}
{{- range .Values.zenml.proxy.additionalNoProxy -}}
{{- $noProxy = printf "%s,%s" $noProxy . -}}
{{- end -}}
{{- /* Add service hostnames if they're not already included */ -}}
{{- if not (contains ".svc" $noProxy) -}}
{{- $noProxy = printf "%s,%s" $noProxy (include "zenml.fullname" .) -}}
{{- $noProxy = printf "%s,%s-dashboard" $noProxy (include "zenml.fullname" .) -}}
{{- end -}}
{{- $noProxy -}}
{{- end -}}
