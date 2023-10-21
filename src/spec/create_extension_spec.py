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
        ],
        contact=[
            "rly@lbl.gov",
            "oruebel@lbl.gov",
            "kay.robbins@utsa.edu",
        ],
    )

    # TODO: specify either the neurodata types that are used by the extension
    # or the namespaces that contain the neurodata types used. Including the
    # namespace will include all neurodata types in that namespace.
    # This is similar to specifying the Python modules that need to be imported
    # to use your new data types.
    # ns_builder.include_type("ElectricalSeries", namespace="core")
    ns_builder.include_namespace("core")

    # TODO: define your new data types
    # see https://pynwb.readthedocs.io/en/latest/extensions.html#extending-nwb
    # for more information
    hed_tags = NWBDatasetSpec(
        neurodata_type_def="HedTags",
        neurodata_type_inc="VectorData",
        doc="An extension of VectorData for Hierarchical Event Descriptor (HED) tags.",
    )

    hed_nwbfile = NWBGroupSpec(
        neurodata_type_def="HedNWBFile",
        neurodata_type_inc="NWBFile",
        doc="An extension of NWBFile to store the Hierarchical Event Descriptor (HED) schema version.",
        attributes=[
            NWBAttributeSpec(
                name="hed_schema_version",
                doc=(
                    "The version of the HED schema used to validate the HED tags, e.g., '8.2.0'. "
                    "Required if HED tags are used in the NWB file."
                ),
                dtype="text",
                required=False,
            ),
        ],
    )

    # TODO: add all of your new data types to this list
    new_data_types = [hed_tags, hed_nwbfile]

    # export the spec to yaml files in the spec folder
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "spec"))
    export_spec(ns_builder, new_data_types, output_dir)
    print("Spec files generated. Please make sure to run `pip install .` to load the changes.")


if __name__ == "__main__":
    # usage: python create_extension_spec.py
    main()
