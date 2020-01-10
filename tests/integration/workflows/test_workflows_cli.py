# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2014-2017 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

from __future__ import absolute_import, division, print_function

from invenio_search import current_search_client as es
from invenio_workflows import ObjectStatus
from invenio_workflows.models import WorkflowObjectModel

from inspirehep.modules.workflows.cli import workflows
from workflow_utils import build_workflow


def test_cli_purges_db_and_es(app_cli_runner):
    indices = ['holdingpen-hep', 'holdingpen-authors']
    build_workflow({}, data_type='hep')
    build_workflow({}, data_type='authors')

    wf_count = WorkflowObjectModel.query.count()
    assert wf_count == 2

    es.indices.refresh(indices)
    es_result = es.search(indices)
    assert es_result['hits']['total']['value'] == 2

    result = app_cli_runner.invoke(workflows, ['purge', '--yes-i-know'])
    assert result.exit_code == 0

    wf_count = WorkflowObjectModel.query.count()
    assert wf_count == 0

    es.indices.refresh(indices)
    es_result = es.search(indices)
    assert es_result['hits']['total']['value'] == 0


def test_cli_restart_by_error_restarts_one_wf_from_current_step(app_cli_runner):
    obj_1 = build_workflow({}, data_type='hep')
    obj_1.status = ObjectStatus.ERROR
    obj_1.extra_data["_error_msg"] = "Error in SendRobotUpload"
    obj_1.save()

    obj_2 = build_workflow({}, data_type='hep')
    obj_2.status = ObjectStatus.ERROR
    obj_2.extra_data["_error_msg"] = "Error in WebColl"
    obj_1.save()

    result = app_cli_runner.invoke(workflows, ['restart_by_error', 'RobotUpload'])
    assert "Found 1 workflows to restart from current step" in result.output_bytes


def test_cli_restart_by_error_restarts_one_wf_from_beginning(
    app_cli_runner
):
    obj_1 = build_workflow({}, data_type='hep')
    obj_1.status = ObjectStatus.ERROR
    obj_1.extra_data["_error_msg"] = "Error in WebColl number 1"
    obj_1.save()

    obj_2 = build_workflow({}, data_type='hep')
    obj_2.status = ObjectStatus.ERROR
    obj_2.extra_data["_error_msg"] = "Error in WebColl number 2"
    obj_1.save()

    result = app_cli_runner.invoke(workflows, ['restart_by_error', 'WebColl', '--from-beginning'])
    output = result.output_bytes

    assert 'Found 2 workflows to restart from first step\n' in output
