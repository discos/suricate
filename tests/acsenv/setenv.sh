#!/usr/bin/env bash

script_name="${BASH_SOURCE[0]}"

if test "$1" && [ "$1" != "introot" ] && [ "$1" != "install" ]
then
    echo "ERROR: wrong argument. Usage:"
    echo "  source $script_name  # To set the environment"
    echo "  source $script_name introot  # To create the introot"
    echo "  source $script_name install  # To install the component"
    return 1
fi

ENVPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTROOTNAME=introot
export INTROOT=$ENVPATH/$INTROOTNAME
source $HOME/.acs/.bash_profile.acs
export ACS_CDB=$ENVPATH


if [ "$1" == "introot" ]
then
    if [ -d "$INTROOT" ]
    then
        echo "The introot directory already exists."
    else
        echo -e "Creating the INTROOT to $INTROOT\n......"
        getTemplateForDirectory INTROOT $INTROOTNAME > /dev/null
    fi
fi
echo "ACS introot and CDB properly configured."


if [ "$1" == "install" ]
then
    # Install the ACS components
    cd $ENVPATH/components/src/
    make clean
    make 
    make install
    cd $ENVPATH
    echo -e "\nOK, you are ready to run ACS :)"
fi
