# -*- coding: utf-8 -*-
import os.path

from pynwb.spec import NWBNamespaceBuilder, export_spec, NWBDatasetSpec, NWBGroupSpec, NWBAttributeSpec

# TODO: import other spec classes as needed
# from pynwb.spec import , NWBLinkSpec, NWBDtypeSpec, NWBRefSpec


def main():
    # these arguments were auto-generated from your cookiecutter inputs
    ns_builder = NWBNamespaceBuilder(
        name="""ndx-hed""",
        version="""0.1.0""",
        doc="""NWB extension for HED data""",
        author=[
            "Ryan Ly",
            "Oliver Ruebel",
            "Kay Robbins",
            "Ian Callanan",
        ],
        contact=[
            "rly@lbl.gov",
            "oruebel@lbl.gov",
            "kay.robbins@utsa.edu",
            "ianrcallanan@gmail.com",
        ],
    )

    ns_builder.include_namespace("core")

    # TODO: define your new data types
    # see https://pynwb.readthedocs.io/en/latest/extensions.html#extending-nwb
    # for more information
    hed_annotations = NWBDatasetSpec(
        name="HED",
        neurodata_type_def="HedAnnotations",
        neurodata_type_inc="VectorData",
        doc=("An extension of VectorData for Hierarchical Event Descriptor (HED) tags. If HED tags are used, "
             "the HED schema version must be specified in the NWB file using the HedVersion type."),
        dtype="text",
        shape=[None],
        dims=['num_hed_strings']
    )

    hed_version = NWBGroupSpec(
        neurodata_type_def="HedVersion",
        neurodata_type_inc="LabMetaData",
        name="HedVersion",  # fixed name
        doc=("An extension of LabMetaData to store the Hierarchical Event Descriptor (HED) schema version. "
             "TODO When merged with core, "
             "this will no longer inherit from LabMetaData but from NWBContainer and be placed "
             "optionally in /general."),
        attributes=[
            NWBAttributeSpec(
                name="hed_version",
                doc=(
                    "The version of the HED schema used to validate the HED tags, e.g., '8.2.0'. "
                    "Required if HED tags are used in the NWB file."
                ),
                dtype='object',
                required=True,
                shape=[None,],
                dims=["n_hed_schema_versions",]
            )
        ],
    )

    # TODO: add all of your new data types to this list
    new_data_types = [hed_annotations, hed_version]

    # export the spec to yaml files in the spec folder
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "spec"))
    export_spec(ns_builder, new_data_types, output_dir)
    print("Spec files generated. Please make sure to run `pip install .` to load the changes.")


if __name__ == "__main__":
    # usage: python create_extension_spec.py
    main()
