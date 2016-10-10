#!/usr/bin/env bash


SCRIPT_PATH="${BASH_SOURCE[0]}";
if ([ -h "${SCRIPT_PATH}" ]) then
  while([ -h "${SCRIPT_PATH}" ]) do SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`; done
fi
pushd . > /dev/null
cd `dirname ${SCRIPT_PATH}` > /dev/null
SCRIPT_PATH=`pwd`;
popd  > /dev/null

WORKING_DIR=$SCRIPT_PATH/../tmp

if [ -d "$WORKING_DIR" ]; then rm -Rf $WORKING_DIR; fi
mkdir $WORKING_DIR
python $SCRIPT_PATH/../run.py > ${WORKING_DIR}/${STACK_NAME}.cfn.json

aws cloudformation create-stack --disable-rollback --stack-name $STACK_NAME --template-body file://${WORKING_DIR}/${STACK_NAME}.cfn.json --parameters file://${SCRIPT_PATH}/../params.json
