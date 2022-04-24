from setuptools import setup

with open("README.rst") as readme, open("CHANGES.rst") as changes:
    setup(
        name="effect-form-validators",
        use_scm_version={
            "version_scheme": "post-release",
            "local_scheme": "node-and-date",
            "relative_to": __file__,
            "root": ".",
        },
        setup_requires=["setuptools_scm"],
        description="Classes for EFFECT trial modelform validation",
        long_description="\n".join((readme.read(), changes.read())),
        long_description_content_type="text/x-rst",
        author="Erik van Widenfelt",
        author_email="ew2789@gmail.com",
        maintainer="Erik van Widenfelt",
        url="https://github.com/effect-trial/effect-form-validators",
        packages=[
            "effect_form_validators",
        ],
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Framework :: Django",
            "Environment :: Web Environment",
            "Intended Audience :: Developers",
            "Framework :: Django",
            "Framework :: Django :: 3.2",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: BSD License",
        ],
        python_requires=">=3.7",
        include_package_data=True,
    )
