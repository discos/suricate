#*****************************************************************
# Positioner Makefile
# ===================
# Marco Buttu <mbuttu@oa-cagliari.inaf.it>
#*****************************************************************

ACSERRDEF= ComponentErrors

ERRXMLFILE= ../idl/ComponentErrors.xml

# Interface
# ----------------------------
CDB_SCHEMAS = Positioner
IDL_FILES = MyNamespaceInterface
MyNamespaceInterfaceStubs_LIBS = baciStubs acscomponentStubs ACSErrTypeCommon \
								 ComponentErrors


# Python directives
PY_PACKAGES = Positioner

# Documentation
MAKE_PDF = ON


# List of all possible C-sources (used to create automatic dependencies)
CSOURCENAMES = \
	$(foreach exe, $(EXECUTABLES) $(EXECUTABLES_L), $($(exe)_OBJECTS)) \
	$(foreach rtos, $(RTAI_MODULES) , $($(rtos)_OBJECTS)) \
	$(foreach lib, $(LIBRARIES) $(LIBRARIES_L), $($(lib)_OBJECTS))


TMP := $(shell searchFile /tmp/tmp.txt)
ifeq ($(TMP),\#error\#)
PERM:=$(shell stat --format=%a $(ERRXMLFILE))
else 
PERM=$(shell cat /tmp/tmp.txt) 
endif


# Include standards
MAKEDIRTMP := $(shell searchFile include/acsMakefile)
ifneq ($(MAKEDIRTMP),\#error\#)
   MAKEDIR := $(MAKEDIRTMP)/include
   include $(MAKEDIR)/acsMakefile
endif


# TARGETS
all:	do_all
	@echo " . . . 'all' done" 

clean : clean_all 
	# Clear INTROOT interface
	$(RM) $(INTROOT)/lib/python/site-packages/MyNamespace*
	# Clear INTROOT Impl
	$(RM) $(INTROOT)/lib/python/site-packages/Positioner*
	$(RM) $(INTROOT)/lib/python/site-packages/libPositionerStubs.*
	# Clear local lib
	$(RM) *~ *Impl/*~ Positioner/*.pyc
	$(RM) ../bin/
	$(RM) ../include/
	$(RM) ../lib/
	$(RM) ../object/
	$(RM) ../rtai/
	@echo " . . . clean done"

clean_dist : clean_all clean_dist_all 
	@echo " . . . clean_dist done"

man   : do_man 
	@echo " . . . man page(s) done"

install : xmlpatch_pre install_all
	@chmod $(PERM) $(ERRXMLFILE)
	@echo "Patch applied" 
	@rm -rf /tmp/tmp.txt
	@echo " . . . installation done"
	@echo " . . . installation done"


xmlpatch_pre :
	@echo "File permissions: " $(PERM)
	@chmod a+w $(ERRXMLFILE)
	@echo $(PERM) > /tmp/tmp.txt
